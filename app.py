"""Streamlit interface for the API Reliability and Latency Analyzer."""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from config.settings import DB_PATH, EXPORT_DIR, DEFAULT_CONCURRENCY_LIMIT
from src import database
from src.endpoint_manager import add_endpoint, edit_endpoint
from src.monitor import run_monitoring
from src.analytics import records_frame, calculate_metrics, endpoint_metrics
from src.anomaly_detection import annotate_anomalies
from src.export import export_logs_csv, export_metrics_csv, export_anomalies_csv
from src.validation import EndpointValidationError

st.set_page_config(page_title='API Reliability Analyzer', page_icon='📡', layout='wide')
database.initialize_database()
st.markdown('''<style>.block-container{padding-top:1.5rem;max-width:1500px}.hero{padding:1.2rem 1.5rem;border:1px solid rgba(128,128,128,.25);border-radius:14px;margin-bottom:1rem}.muted{opacity:.7}</style>''',unsafe_allow_html=True)
st.title('📡 API Reliability & Latency Analyzer')
st.caption('Local-first API monitoring, historical analytics, and explainable latency anomaly detection.')
endpoints=database.list_endpoints()
if not endpoints:
    st.info('No endpoints configured yet. Add one in **Endpoint Management** or use the local test server.')
page=st.sidebar.radio('Navigation',['Overview','Endpoint Management','Run Monitoring','Historical Analytics','Anomaly Detection','Endpoint Comparison','Data Export','Settings & About'])

def frame(): return records_frame(database.query_logs())
def fmt(value, suffix=''):
    return '—' if value is None or pd.isna(value) else f'{value:.2f}{suffix}'

if page=='Overview':
    df=frame(); metrics=calculate_metrics(df); enabled=sum(bool(e['enabled']) for e in endpoints)
    c=st.columns(4); c[0].metric('Configured endpoints',len(endpoints)); c[1].metric('Enabled endpoints',enabled); c[2].metric('Overall success rate',fmt(metrics['success_rate_pct'],'%')); c[3].metric('Recent failures',int((~df['success'].astype(bool)).sum()) if not df.empty else 0)
    c=st.columns(4); c[0].metric('Median latency',fmt(metrics['median_latency_ms'],' ms')); c[1].metric('P95 latency',fmt(metrics['p95_latency_ms'],' ms')); c[2].metric('Monitoring attempts',metrics['total_attempts']); c[3].metric('Detected anomalies','—' if df.empty else int(annotate_anomalies(df,'iqr')['is_anomaly'].sum()))
    st.subheader('Recent monitoring activity')
    runs=database.query_runs(limit=10)
    if runs: st.dataframe(pd.DataFrame(runs),use_container_width=True,hide_index=True)
    else: st.info('No runs yet. Monitoring starts only when you press the Run Monitoring button.')
    if not df.empty:
        df=df.sort_values('timestamp'); st.plotly_chart(px.line(df,x='timestamp',y='response_time_ms',color='endpoint_name',title='Observed latency over time',labels={'timestamp':'Timestamp (UTC)','response_time_ms':'Latency (ms)','endpoint_name':'Endpoint'}),use_container_width=True)
elif page=='Endpoint Management':
    st.subheader('Configured endpoints')
    if endpoints: st.dataframe(pd.DataFrame(endpoints),use_container_width=True,hide_index=True)
    with st.expander('Add endpoint',expanded=not endpoints):
        with st.form('add_endpoint'):
            name=st.text_input('Friendly name'); url=st.text_input('URL',placeholder='https://example.com/health'); method=st.selectbox('HTTP method',['GET','HEAD']); timeout=st.number_input('Timeout (seconds)',min_value=.1,max_value=60.,value=5.,step=.5); low=st.number_input('Expected status minimum',100,599,200); high=st.number_input('Expected status maximum',100,599,299); local=st.checkbox('Allow localhost/private destination for trusted local testing',value=False); submitted=st.form_submit_button('Add endpoint')
        if submitted:
            try:
                eid=add_endpoint(name,url,method,timeout,True,low,high,local); st.success(f'Endpoint added (ID {eid}).'); st.rerun()
            except (ValueError,EndpointValidationError) as exc: st.error(str(exc))
    if endpoints:
        ids={f"{e['id']} — {e['name']}":e for e in endpoints}
        selected_label=st.selectbox('Select endpoint to edit or disable',list(ids)); selected=ids[selected_label]
        with st.form('edit_endpoint'):
            name=st.text_input('Name',selected['name']); url=st.text_input('URL',selected['url']); method=st.selectbox('Method',['GET','HEAD'],index=['GET','HEAD'].index(selected['method'])); timeout=st.number_input('Timeout seconds',.1,60.,float(selected['timeout_seconds']),.5); low=st.number_input('Expected status min',100,599,int(selected['expected_status_min'])); high=st.number_input('Expected status max',100,599,int(selected['expected_status_max'])); enabled=st.checkbox('Enabled',bool(selected['enabled'])); local=st.checkbox('Allow local/private destination for trusted local testing',False); save=st.form_submit_button('Save changes')
        if save:
            try:
                edit_endpoint(selected['id'],name,url,method,timeout,enabled,low,high,local); st.success('Endpoint updated.'); st.rerun()
            except ValueError as exc: st.error(str(exc))
        if st.button('Remove endpoint configuration',type='secondary',help='Historical records are retained, so endpoints with history cannot be physically deleted. Disable it instead.'):
            try:
                removed=database.delete_endpoint(selected['id'])
                st.success('Endpoint removed.') if removed else st.warning('Endpoint not found.'); st.rerun()
            except Exception: st.error('This endpoint has historical monitoring records and cannot be physically deleted without losing referential integrity. Disable it to stop monitoring; historical records remain available.')
elif page=='Run Monitoring':
    st.subheader('Start a one-shot monitoring run')
    enabled=[e for e in endpoints if e['enabled']]
    if not enabled: st.warning('No enabled endpoints. Enable one in Endpoint Management first.')
    else:
        labels={f"{e['id']} — {e['name']} ({e['url']})":e for e in enabled}; chosen=st.multiselect('Endpoints to monitor',list(labels),default=list(labels)); mode=st.radio('Execution mode',['concurrent','sequential'],horizontal=True); limit=st.slider('Concurrency limit',1,20,DEFAULT_CONCURRENCY_LIMIT,disabled=mode=='sequential'); local=st.checkbox('Allow local/private destinations (trusted local testing only)',False)
        if st.button('▶ Run monitoring now',type='primary',disabled=not chosen):
            with st.spinner('Monitoring selected endpoints…'):
                try:
                    result=run_monitoring([labels[x] for x in chosen],mode,limit,allow_local=local)
                    st.session_state['last_run']=result
                    st.success(f"Run #{result['run_id']} {result['run_status']} in {result['elapsed_seconds']:.3f} seconds.")
                except Exception as exc: st.error(f'Monitoring run could not be saved: {type(exc).__name__}: {str(exc)[:200]}')
    result=st.session_state.get('last_run')
    if result and result['records']:
        st.dataframe(pd.DataFrame(result['records']),use_container_width=True,hide_index=True)
elif page=='Historical Analytics':
    df=frame(); st.subheader('Historical analytics')
    if df.empty: st.info('No monitoring history yet. Run a monitor or generate synthetic sample data for offline notebook analysis.')
    else:
        names=['All endpoints']+sorted(df['endpoint_name'].dropna().unique().tolist()); name=st.selectbox('Endpoint',names); df=df if name=='All endpoints' else df[df['endpoint_name']==name]
        start=pd.to_datetime(df['timestamp'],utc=True).min().date(); end=pd.to_datetime(df['timestamp'],utc=True).max().date(); d1,d2=st.columns(2); start_date=d1.date_input('Start date (UTC)',start); end_date=d2.date_input('End date (UTC)',end)
        df=df[(df['timestamp'].dt.date>=start_date)&(df['timestamp'].dt.date<=end_date)]
        m=calculate_metrics(df); cols=st.columns(4); cols[0].metric('Attempts',m['total_attempts']); cols[1].metric('Success rate',fmt(m['success_rate_pct'],'%')); cols[2].metric('Median',fmt(m['median_latency_ms'],' ms')); cols[3].metric('P95',fmt(m['p95_latency_ms'],' ms'))
        st.plotly_chart(px.line(df.sort_values('timestamp'),x='timestamp',y='response_time_ms',color='endpoint_name',title='Latency over time',labels={'timestamp':'Timestamp (UTC)','response_time_ms':'Latency (ms)'}),use_container_width=True)
        st.plotly_chart(px.histogram(df,x='response_time_ms',color='endpoint_name',title='Latency distribution',labels={'response_time_ms':'Latency (ms)'}),use_container_width=True)
        status=df['status_code'].fillna('No HTTP response').astype(str).value_counts().rename_axis('status').reset_index(name='count'); st.plotly_chart(px.bar(status,x='status',y='count',title='HTTP status / no-response distribution',labels={'status':'HTTP status','count':'Attempts'}),use_container_width=True)
        cats=df['failure_category'].fillna('success').value_counts().rename_axis('category').reset_index(name='count'); st.plotly_chart(px.bar(cats,x='category',y='count',title='Failure-category breakdown',labels={'category':'Category','count':'Attempts'}),use_container_width=True)
elif page=='Anomaly Detection':
    df=frame(); st.subheader('Latency anomaly detection')
    if df.empty: st.info('No monitoring data available.');
    else:
        names=sorted(df['endpoint_name'].dropna().unique()); name=st.selectbox('Endpoint',names); method=st.selectbox('Method',['iqr','rolling_median']); subset=df[df['endpoint_name']==name].sort_values('timestamp'); subset=subset[subset['response_time_ms'].notna()]
        if method=='iqr': k=st.slider('IQR multiplier k',1.,4.,1.5,.25); result=annotate_anomalies(subset,method,k=k)
        else: window=st.slider('Historical window size',3,50,10); minimum=st.slider('Minimum historical observations',2,window,5); sensitivity=st.slider('Sensitivity multiplier',1.,5.,3.,.25); result=annotate_anomalies(subset,method,window_size=window,min_observations=minimum,sensitivity=sensitivity)
        anomalies=result[result['is_anomaly']]; st.metric('Flagged observations',len(anomalies)); st.caption('A statistical anomaly is unusual relative to the selected baseline; it does not necessarily indicate an API failure.')
        if anomalies.empty: st.info('No anomalies were flagged with the current settings.')
        else: st.dataframe(anomalies,use_container_width=True,hide_index=True)
        st.plotly_chart(px.scatter(result,x='timestamp',y='response_time_ms',color='is_anomaly',title=f'Latency anomalies ({method})',labels={'timestamp':'Timestamp (UTC)','response_time_ms':'Latency (ms)','is_anomaly':'Flagged'}),use_container_width=True)
elif page=='Endpoint Comparison':
    df=frame(); st.subheader('Endpoint comparison')
    if df.empty: st.info('No history available to compare.')
    else:
        comparison=endpoint_metrics(df); comparison['observation_start_utc']=df.groupby('endpoint_id')['timestamp'].min().values; comparison['observation_end_utc']=df.groupby('endpoint_id')['timestamp'].max().values; st.dataframe(comparison,use_container_width=True,hide_index=True); st.caption('Compare sample counts and observation periods before interpreting differences. These are observed samples, not guaranteed long-term uptime.')
        st.plotly_chart(px.bar(comparison,x='endpoint_name',y='success_rate_pct',title='Observed success rate by endpoint',labels={'endpoint_name':'Endpoint','success_rate_pct':'Success rate (%)'}),use_container_width=True)
        st.plotly_chart(px.bar(comparison,x='endpoint_name',y='median_latency_ms',title='Median latency by endpoint',labels={'endpoint_name':'Endpoint','median_latency_ms':'Median latency (ms)'}),use_container_width=True)
elif page=='Data Export':
    st.subheader('Export monitoring data')
    EXPORT_DIR.mkdir(parents=True,exist_ok=True)
    for label,func,filename in [('Raw monitoring records','logs','monitoring_records.csv'),('Aggregated endpoint metrics','metrics','endpoint_metrics.csv'),('Anomaly records','anomalies','anomaly_records.csv')]:
        if st.button(f'Generate {label} CSV',key=label):
            path=EXPORT_DIR/filename
            if func=='logs': export_logs_csv(DB_PATH,path)
            elif func=='metrics': export_metrics_csv(DB_PATH,path)
            else: export_anomalies_csv(DB_PATH,path,method='iqr')
            st.session_state['export_path']=str(path)
        if st.session_state.get('export_path')==str(EXPORT_DIR/filename) and Path(st.session_state['export_path']).exists():
            data=Path(st.session_state['export_path']).read_bytes(); st.download_button(f'Download {filename}',data,file_name=filename,mime='text/csv',key='download_'+filename)
    st.caption('Empty exports contain column headers when available and do not fabricate rows.')
else:
    st.subheader('Settings & About')
    st.markdown('''**Purpose:** local-first monitoring of HTTP response status, latency, failures, and historical trends.\n\n**Data store:** SQLite (`data/api_monitoring.db`).\n\n**Security:** only HTTP/HTTPS URLs are accepted. Private/loopback destinations are blocked unless you explicitly opt into local testing for a trusted server. Redirects are disabled to avoid following an unvalidated destination. URL validation is best-effort; DNS rebinding and infrastructure-specific routing require network-level controls for stronger protection.\n\n**Interpretation:** response latency is measured with a monotonic clock. Failed requests remain in reliability rates; latency summaries include only attempts with a measured elapsed time. P95 uses NumPy's linear percentile convention.\n\n**No automatic polling:** this app sends requests only after an explicit user action.''')
    st.write('Database location:',str(DB_PATH)); st.write('Configured endpoints:',len(endpoints)); st.write('Python / Streamlit:',__import__('sys').version.split()[0],st.__version__)
