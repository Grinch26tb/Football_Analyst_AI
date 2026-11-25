import streamlit as st
import pandas as pd
from urllib.request import urlopen, Request
from io import BytesIO
from datetime import date

st.set_page_config(page_title='Football Analytics AI 3.0', page_icon='⚽', layout='centered')
st.markdown('''<style>.stApp {background-color:#101827;color:#e5e7eb;} [data-testid="stHeader"] {background:#101827;} h1,h2,h3,p,label {color:#e5e7eb !important;}</style>''',unsafe_allow_html=True)
st.title('⚽ Football Analytics AI 3.0')
st.caption('Analisi descrittiva dei risultati storici')
leagues={'Serie A':'I1','Serie B':'I2','Premier League':'E0','Liga':'SP1','Bundesliga':'D1','Ligue 1':'F1'}
cols=['Data','Casa','Trasferta','GolCasa','GolTrasferta']
@st.cache_data(ttl=3600)
def load(url):
    with urlopen(Request(url,headers={'User-Agent':'Football Analytics historical viewer'}),timeout=25) as r:
        return pd.read_csv(BytesIO(r.read()),encoding='latin1')
source=st.radio('Fonte dati',['CSV personale','Archivio online'],index=1,horizontal=True)
if source=='Archivio online':
    league=st.selectbox('Campionato',list(leagues))
    year=st.selectbox('Stagione',list(range(date.today().year if date.today().month>=7 else date.today().year-1,2018,-1)),format_func=lambda y:f'{y}/{y+1}')
    url=f'https://www.football-data.co.uk/mmz4281/{year%100:02d}{(year+1)%100:02d}/{leagues[league]}.csv'
    st.caption('Fonte: Football-Data.co.uk. Usa questa fonte solo se le condizioni di utilizzo lo consentono.')
    st.markdown('[Archivio originale](https://www.football-data.co.uk/data.php)')
    if not st.checkbox('Ho verificato le condizioni di utilizzo della fonte'):
        st.stop()
    if st.button('Ricarica archivio'):
        load.clear()
    try:
        raw=load(url)
    except Exception:
        st.error('Archivio non raggiungibile. Riprova oppure usa un CSV personale.')
        st.stop()
else:
    f=st.file_uploader('Carica risultati storici CSV',type=['csv'])
    st.download_button('Scarica modello CSV','Data,Casa,Trasferta,GolCasa,GolTrasferta\n','modello.csv','text/csv')
    if f is None:
        st.info('Carica un CSV oppure scegli Archivio online.')
        st.stop()
    try:
        raw=pd.read_csv(f)
    except Exception:
        st.error('CSV non leggibile.'); st.stop()
try:
    d=raw.rename(columns=dict(Date='Data',HomeTeam='Casa',AwayTeam='Trasferta',FTHG='GolCasa',FTAG='GolTrasferta'))[cols].copy()
    d['Data']=pd.to_datetime(d.Data,format='mixed',dayfirst=True,errors='coerce')
    for c in ['GolCasa','GolTrasferta']:
        d[c]=pd.to_numeric(d[c],errors='coerce')
    d=d.dropna().copy()
    d=d[(d.Data.dt.date<=date.today())&(d.Casa!=d.Trasferta)]
    for c in ['GolCasa','GolTrasferta']:
        d=d[(d[c]>=0)&(d[c]%1==0)]
        d[c]=d[c].astype(int)
    d=d.drop_duplicates().sort_values('Data')
    if d.empty: raise ValueError()
except Exception:
    st.error('Nessun risultato valido o colonne CSV mancanti.'); st.stop()
a=d[['Data','Casa','GolCasa','GolTrasferta']].set_axis(['Data','Squadra','Fatti','Subiti'],axis=1).assign(Campo='Casa')
b=d[['Data','Trasferta','GolTrasferta','GolCasa']].set_axis(['Data','Squadra','Fatti','Subiti'],axis=1).assign(Campo='Trasferta')
t=pd.concat([a,b],ignore_index=True).sort_values('Data')
t['Vittorie']=(t.Fatti>t.Subiti).astype(int)
t['Pareggi']=(t.Fatti==t.Subiti).astype(int)
t['Sconfitte']=(t.Fatti<t.Subiti).astype(int)
def summary(x):
    s=x.groupby('Squadra').agg(Partite=('Fatti','size'),Gol_fatti=('Fatti','sum'),Gol_subiti=('Subiti','sum'),Vittorie=('Vittorie','sum'),Pareggi=('Pareggi','sum'),Sconfitte=('Sconfitte','sum'))
    s['Punti']=3*s.Vittorie+s.Pareggi
    s['Differenza reti']=s.Gol_fatti-s.Gol_subiti
    return s.sort_values(['Punti','Differenza reti','Gol_fatti'],ascending=False)
s=summary(t)
st.caption(f'Risultati dal {d.Data.min():%d/%m/%Y} al {d.Data.max():%d/%m/%Y}')
page=st.radio('Sezione',['Dashboard','Squadre','Confronto','Archivio','Verifica storica'],horizontal=True)
if page=='Dashboard':
    c1,c2=st.columns(2); c1.metric('Partite',len(d)); c2.metric('Gol totali',int(d.GolCasa.sum()+d.GolTrasferta.sum()))
    st.caption('Graduatoria calcolata dai risultati: non considera penalizzazioni o criteri ufficiali di spareggio.')
    st.dataframe(s)
    st.metric('Media gol per partita',f'{(d.GolCasa+d.GolTrasferta).mean():.2f}')
    st.bar_chart(s[['Gol_fatti','Gol_subiti']])
elif page=='Squadre':
    team=st.selectbox('Squadra',sorted(s.index))
    x=t[t.Squadra==team]
    campo=st.radio('Campo',['Tutti','Casa','Trasferta'],horizontal=True)
    if campo!='Tutti': x=x[x.Campo==campo]
    n=st.selectbox('Periodo',['Tutte',5,10]); x=x if n=='Tutte' else x.tail(n)
    st.dataframe(summary(x)); st.line_chart(x.groupby('Data')[['Fatti','Subiti']].sum()); st.dataframe(x.drop(columns='Squadra'),hide_index=True)
elif page=='Confronto':
    teams=st.multiselect('Squadre',sorted(s.index),default=list(s.index[:2]))
    if teams:
        st.bar_chart(s.loc[teams,['Gol_fatti','Gol_subiti']]); st.dataframe(s.loc[teams])
    if len(teams)==2:
        st.subheader('Scontri diretti nella stagione selezionata')
        st.dataframe(d[d.Casa.isin(teams)&d.Trasferta.isin(teams)],hide_index=True)
elif page=='Verifica storica':
    from math import exp, factorial
    st.subheader('Esperimento storico: Poisson')
    st.caption('Modello didattico di campionato, senza quote o previsioni future. Ogni giornata usa soltanto risultati di date precedenti.')
    records=[]
    past=d.iloc[:0]
    for day, games in d.groupby('Data',sort=True):
        if len(past)>=50:
            h=float(past.GolCasa.mean()); a=float(past.GolTrasferta.mean())
            ph=[exp(-h)*h**k/factorial(k) for k in range(16)]
            pa=[exp(-a)*a**k/factorial(k) for k in range(16)]
            probs=[sum(ph[i]*pa[j] for i in range(16) for j in range(16) if i>j),sum(ph[i]*pa[i] for i in range(16)),sum(ph[i]*pa[j] for i in range(16) for j in range(16) if i<j)]
            probs=[v/sum(probs) for v in probs]
            pred=max(range(3),key=lambda k:probs[k])
            base=max(range(3),key=lambda k:[(past.GolCasa>past.GolTrasferta).sum(),(past.GolCasa==past.GolTrasferta).sum(),(past.GolCasa<past.GolTrasferta).sum()][k])
            for g in games.itertuples():
                actual=0 if g.GolCasa>g.GolTrasferta else 1 if g.GolCasa==g.GolTrasferta else 2
                records.append((pred==actual,base==actual,sum((v-int(k==actual))**2 for k,v in enumerate(probs))))
        past=pd.concat([past,games],ignore_index=True)
    if records:
        r=pd.DataFrame(records,columns=['Modello','Riferimento','Brier'])
        st.metric('Partite valutate',len(r))
        st.metric('Accuratezza storica',f'{r.Modello.mean():.1%}')
        st.metric('Riferimento: esito più frequente',f'{r.Riferimento.mean():.1%}')
        st.metric('Brier score (0 = ideale)',f'{r.Brier.mean():.3f}')
        st.caption('Le prime 50 o più partite servono da storico iniziale. Accuratezza passata non garantisce risultati futuri.')
    else:
        st.info('Servono almeno 50 partite precedenti e una data successiva per il test.')
else:
    st.dataframe(d.sort_values('Data',ascending=False),hide_index=True)
