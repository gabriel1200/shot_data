"""Build league shot-zone averages conditioned on shot context.

The existing team/<year>[ps]/avg.csv is left unchanged. Each output uses the
same shooting-team chart rows and NBA zone labels as that file. Run from the
shot_data root with --root .; the default --out writes context/averages.
"""
import argparse
import csv
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ZONES = ('SHOT_ZONE_BASIC', 'SHOT_ZONE_AREA', 'SHOT_ZONE_RANGE')
LABELS = ('fastbreak', '2ndchance', 'fromturnover', 'pointsinthepaint')


def rows(path):
    with path.open(newline='') as f:
        yield from csv.DictReader(f)


def count(counter, category, zone, made):
    counter[(category, *zone)][0] += 1
    counter[(category, *zone)][1] += made


def write(path, dimension, counts):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(('GRID_TYPE', dimension, *ZONES, 'FGA', 'FGM', 'FG_PCT'))
        for (category, *zone), (fga, fgm) in sorted(counts.items()):
            pct = (Decimal(fgm) / Decimal(fga)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
            writer.writerow(('League Averages', category, *zone, fga, fgm, f'{pct:.3f}'))


def build(root, out, year, tag):
    season_dir = root / 'team' / f'{year}{"ps" if tag == "po" else ""}'
    context_path = root / 'context' / f'{year}_{tag}.csv'
    context = {}
    for row in rows(context_path):
        key = (row['GAME_ID'], row['GAME_EVENT_ID'])
        if key in context:
            raise ValueError(f'duplicate context key {year} {tag} {key}')
        context[key] = row

    phase_counts = defaultdict(lambda: [0, 0])
    qualifier_counts = defaultdict(lambda: [0, 0])
    base_counts = defaultdict(lambda: [0, 0])
    seen = set()
    missing_context = 0
    for path in sorted(season_dir.glob('*.csv')):
        if path.name == 'avg.csv' or path.stem.endswith('vs'):
            continue
        for row in rows(path):
            key = (row['GAME_ID'], row['GAME_EVENT_ID'])
            if key in seen:
                raise ValueError(f'duplicate shot key {year} {tag} {key}')
            seen.add(key)
            zone = tuple(row[z] for z in ZONES)
            made = int(row['SHOT_MADE_FLAG'])
            base_counts[zone][0] += 1
            base_counts[zone][1] += made
            ctx = context.get(key)
            if ctx is None:
                missing_context += 1
            phase = ctx['PHASE'] if ctx and ctx['PHASE'] else 'unclassified'
            count(phase_counts, 'all', zone, made)
            count(phase_counts, phase, zone, made)
            if year >= 2021:
                count(qualifier_counts, 'all', zone, made)
                if ctx is None:
                    count(qualifier_counts, 'unmatched', zone, made)
                elif not ctx['QUALIFIERS']:
                    count(qualifier_counts, 'none', zone, made)
                else:
                    labels = ctx['QUALIFIERS'].split('|')
                    if len(labels) != len(set(labels)) or any(label not in LABELS for label in labels):
                        raise ValueError(f'invalid qualifiers {year} {tag} {key}: {labels}')
                    count(qualifier_counts, 'any', zone, made)
                    for label in labels:
                        count(qualifier_counts, label, zone, made)

    existing = {tuple(row[z] for z in ZONES): (int(row['FGA']), int(row['FGM']))
                for row in rows(season_dir / 'avg.csv')}
    actual = {zone: tuple(counts) for zone, counts in base_counts.items()}
    if actual != existing:
        diff = [(zone, actual.get(zone), existing.get(zone)) for zone in set(actual) | set(existing)
                if actual.get(zone) != existing.get(zone)]
        raise ValueError(f'base avg disagrees with chart rows for {year} {tag}: {diff[:5]}')
    write(out / f'{year}_{tag}_phase.csv', 'PHASE', phase_counts)
    if year >= 2021:
        write(out / f'{year}_{tag}_qualifier.csv', 'QUALIFIER', qualifier_counts)
    return {'year': year, 'tag': tag, 'shots': len(seen), 'missing_context': missing_context,
            'phase_unclassified': sum(v[0] for (category, *_), v in phase_counts.items() if category == 'unclassified')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--out', type=Path, default=Path('context/averages'))
    parser.add_argument('--years', nargs='*', type=int, default=range(1997, 2027))
    args = parser.parse_args()
    report = [build(args.root, args.out, year, tag) for year in args.years for tag in ('rs', 'po')]
    print(f"{len(report)} partitions, {sum(x['shots'] for x in report):,} shots, "
          f"{sum(x['missing_context'] for x in report):,} keys without context, "
          f"{sum(x['phase_unclassified'] for x in report):,} unclassified phases")
