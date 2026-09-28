"""Hallazgos descriptivos del historial; no infiere salud ni fuentes ausentes."""
import pandas as pd


def prepared(df):
    d = df.sort_values('ts', kind='stable').copy()
    # Desconocido no equivale a no-skip.
    d['skip_known'] = d['skipped'].map(lambda x: isinstance(x, (bool, int)) and x in (0, 1))
    d['skip_value'] = d['skipped'].where(d['skip_known']).astype('Float64')
    return d


def curious_findings(df, min_plays=10):
    d = prepared(df)
    night = d[d['hour'].between(2, 4)]
    songs = night.groupby(['track', 'artist']).size().sort_values(ascending=False)
    nocturnal = None if songs.empty else dict(track=songs.index[0][0], artist=songs.index[0][1], plays=int(songs.iloc[0]))
    days = d.groupby('date').agg(plays=('ts', 'size'), known=('skip_value', 'count'), skips=('skip_value', 'sum'))
    days['rate'] = days['skips'] / days['known'].replace(0, float('nan'))
    chaos = days[(days['known'] >= min_plays) & (days['rate'] > .7)].sort_values(['rate', 'skips'], ascending=False)
    artists = d.groupby('artist').agg(plays=('ts', 'size'), known=('skip_value', 'count'), skips=('skip_value', 'sum'))
    artists['rate'] = artists['skips'] / artists['known'].replace(0, float('nan'))
    # Among the ten most played artists, rank by skip count then volume.
    candidates = artists[artists['known'] >= min_plays].sort_values('plays', ascending=False).head(10)
    love_hate = candidates[candidates['skips'] > 0].sort_values(['skips', 'plays'], ascending=False)
    # Compute runs BEFORE filtering hours; another song, another date or a >30 min gap breaks a run.
    same = d[['track', 'artist']].eq(d[['track', 'artist']].shift()).all(axis=1)
    inside = d['hour'].between(2, 4)
    contiguous = (same & inside & inside.shift(fill_value=False) &
                  d['date'].eq(d['date'].shift()) & d['ts'].diff().le(pd.Timedelta(minutes=30)))
    d['run'] = (~contiguous).cumsum()
    runs = d[inside].groupby('run').agg(track=('track', 'first'), artist=('artist', 'first'),
                                     start=('ts', 'min'), end=('ts', 'max'), plays=('ts', 'size'))
    loops = runs[runs['plays'] >= 3].sort_values('plays', ascending=False)
    return dict(nocturnal=nocturnal, chaos=chaos, love_hate=love_hate, artists=artists, loops=loops)


def yearly_evolution(df, top_n=5):
    d = df.copy()
    d['year'] = d['ts'].dt.year
    d['artist'] = d['artist'].fillna('Sin artista identificado')
    totals = d.groupby('year').size()
    counts = d.groupby(['year', 'artist']).size().rename('plays').reset_index()
    # Union of each year's leaders: old favorites do not disappear behind overall leaders.
    leaders = counts.sort_values('plays', ascending=False).groupby('year').head(top_n)
    selected = sorted(leaders['artist'].unique())
    d['group'] = d['artist'].where(d['artist'].isin(selected), 'Otros artistas (agrupados)')
    grouped = d.groupby(['year', 'group']).size().unstack(fill_value=0)
    shares = grouped.div(totals, axis=0).mul(100).stack().rename('Porcentaje').reset_index()
    shares = shares.rename(columns={'year': 'Año', 'group': 'Artista'})
    summary = d.groupby('year').agg(plays=('ts', 'size'), first=('ts', 'min'), last=('ts', 'max'), days=('date', 'nunique'))
    top = counts.sort_values(['year', 'plays', 'artist'], ascending=[True, False, True]).groupby('year').head(1).set_index('year')
    summary['leader'] = top['artist']
    summary['leader_share'] = top['plays'] / totals * 100
    return shares, summary


def night_contrast(df):
    d = prepared(df)
    # Adjacent in full chronology, same local date, at most 30 minutes apart.
    d['repeat'] = (d[['track', 'artist']].eq(d[['track', 'artist']].shift()).all(axis=1) &
                   d['date'].eq(d['date'].shift()) & d['ts'].diff().le(pd.Timedelta(minutes=30)))
    masks = {'Tardes laborables (12–18 h)': (d['ts'].dt.dayofweek < 5) & d['hour'].between(12, 17),
             'Madrugada (02–05 h)': d['hour'].between(2, 4)}
    result = []
    for name, mask in masks.items():
        sub = d[mask]
        result.append(dict(Franja=name, Reproducciones=len(sub), Saltos_conocidos=int(sub['skip_value'].count()),
                           Skip_pct=float(sub['skip_value'].mean())*100 if sub['skip_value'].count() else None,
                           Repetición_pct=sub['repeat'].mean()*100 if len(sub) else None,
                           Segundos_escuchados=sub['ms_played'].mean()/1000 if len(sub) else None))
    return pd.DataFrame(result)


def playback_signals(df):
    mapping = {'clickrow': 'Selección explícita (clickrow)', 'playbtn': 'Botón de reproducción (playbtn)',
               'fwdbtn': 'Avance manual (fwdbtn)', 'backbtn': 'Retroceso manual (backbtn)',
               'trackdone': 'Continuación tras fin de pista (trackdone)'}
    raw = df['reason_start'].fillna('sin dato').astype(str)
    labels = raw.map(mapping).fillna('Origen no identificable')
    table = labels.value_counts().rename_axis('Señal').reset_index(name='Reproducciones')
    table['Porcentaje'] = table['Reproducciones'] / len(df) * 100 if len(df) else 0
    return table, raw.value_counts().rename_axis('reason_start').reset_index(name='Reproducciones')
