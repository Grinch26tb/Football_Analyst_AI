import streamlit as st
import pandas as pd
import io
st.set_page_config(page_title='Football Analytics AI',page_icon='⚽',layout='centered')
st.title('⚽ Football Analytics AI')
st.caption('Analisi descrittiva delle partite già disputate')
example='Data,Casa,Trasferta,GolCasa,GolTrasferta\n2024-01-01,Alfa,Beta,2,1\n2024-01-08,Beta,Gamma,0,0\n2024-01-15,Gamma,Alfa,1,3\n2024-01-22,Beta,Alfa,2,2\n2024-01-29,Alfa,Gamma,1,0\n'
f=st.file_uploader('Carica un CSV di risultati storici',type=['csv'])
st.download_button('Scarica CSV di esempio',example,'esempio.csv','text/csv')
try:
 d=pd.read_csv(f if f else io.StringIO(example))
 d=d[['Data','Casa','Trasferta','GolCasa','GolTrasferta']].copy()
 d['Data']=pd.to_datetime(d.Data,errors='raise')
 for c in ['GolCasa','GolTrasferta']:
  d[c]=pd.to_numeric(d[c],errors='raise')
  if d[c].isna().any() or (d[c]<0).any() or (d[c]%1!=0).any(): raise ValueError('Gol non validi')
 if d.empty or d[['Data','Casa','Trasferta']].isna().any().any() or (d.Casa==d.Trasferta).any() or (d.Data.dt.date>pd.Timestamp.today().date()).any(): raise ValueError('Dati non validi')
except Exception:
 st.error('CSV non valido. Usa le colonne del file di esempio e solo risultati conclusi.'); st.stop()
if not f: st.info('Stai visualizzando dati inventati a scopo dimostrativo.')
a=d[['Data','Casa','GolCasa','GolTrasferta']].set_axis(['Data','Squadra','Fatti','Subiti'],axis=1)
b=d[['Data','Trasferta','GolTrasferta','GolCasa']].set_axis(['Data','Squadra','Fatti','Subiti'],axis=1)
t=pd.concat([a,b],ignore_index=True).sort_values('Data')
t['Vittorie']=(t.Fatti>t.Subiti).astype(int)
t['Pareggi']=(t.Fatti==t.Subiti).astype(int)
t['Sconfitte']=(t.Fatti<t.Subiti).astype(int)
summary=t.groupby('Squadra').agg(Partite=('Fatti','size'),Gol_fatti=('Fatti','sum'),Gol_subiti=('Subiti','sum'),Vittorie=('Vittorie','sum'),Pareggi=('Pareggi','sum'),Sconfitte=('Sconfitte','sum'))
page=st.radio('Sezione',['Dashboard','Squadre','Confronto','Archivio'],horizontal=True)
if page=='Dashboard':
 c1,c2=st.columns(2); c1.metric('Partite',len(d)); c2.metric('Gol totali',int(d.GolCasa.sum()+d.GolTrasferta.sum()))
 st.dataframe(summary,use_container_width=True)
elif page=='Squadre':
 s=st.selectbox('Squadra',summary.index); x=t[t.Squadra==s]; st.dataframe(summary.loc[[s]]); st.line_chart(x.groupby('Data')[['Fatti','Subiti']].sum()); st.dataframe(x.drop(columns='Squadra'),hide_index=True)
elif page=='Confronto':
 s=st.multiselect('Squadre',summary.index,default=list(summary.index[:2])); st.bar_chart(summary.loc[s,['Gol_fatti','Gol_subiti']]); st.dataframe(summary.loc[s])
else:
 st.dataframe(d.sort_values('Data',ascending=False),hide_index=True)
