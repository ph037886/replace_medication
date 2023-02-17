#python 3.10.8 64位元

import streamlit as st
import pandas as pd

def replace_same_form_atc(form, atc, origanal_diacode):
    med_his=pd.read_pickle(r'his_med.pkl')
    mask_form=med_his['醫令碼'].str.startswith(form)==True #只查同劑型分類的
    mask_atc=med_his['ATC_CODE'].str.startswith(str(atc))==True #ATC code有包含的
    without_organal=med_his['醫令碼']!=origanal_diacode #排除查詢藥品自己
    replace=med_his[mask_atc & mask_form & without_organal]
    return replace

def atc_class_med(form,atc,origanal_diacode):
    class_list=[7,5,4,3,1] #atc code拆開
    class_dict=dict() #做一個字典接收資料，key是atc code，value是品項的df
    for i in class_list:
        atc_slice=atc[:i] #atc code做片切
        class_dict[atc_slice]=replace_same_form_atc(form, atc_slice,origanal_diacode)
    return class_dict

def keyword_find(keyword):
    med_his=pd.read_pickle(r'his_med.pkl')
    mask_diacaode=med_his['醫令碼'].str.upper().str.contains(str(keyword).upper())==True
    mask_chname=med_his['學名'].str.upper().str.contains(str(keyword).upper())==True
    mask_egname=med_his['商品名'].str.upper().str.contains(str(keyword).upper())==True
    mask_cname=med_his['中文名'].str.upper().str.contains(str(keyword).upper())==True
    result=med_his[mask_diacaode | mask_chname | mask_egname | mask_cname] #用or混合查詢
    return result

def df_show(final_dict): #顯示結果的功能
    global search_result_container,final_result_container
    #資料來源是字典
    for atc, df in final_dict.items():
        df=df[df['DC_TYPE'].str.upper().str.contains('N')==True] #有包含N的代表至少門急住有任意一個地方有開檔
        df=df.drop(columns=['DC_TYPE']) #刪掉不要欄位
        df=df[['醫令碼','商品名','中文名','學名','ATC_CODE','櫃位']]
        final_result_container.header(atc)
        if df.empty==True:
            final_result_container.warning('本ATC code階層，本院目前無相同ATC code藥品，請找更後面階層藥品', icon="⚠️")
        else:
            final_result_container.dataframe(df.set_index('醫令碼')) #設定醫令碼為index，避免原始index被誤會為存量

def search_event(keyword):
    global result_egname_list,search_result_container,final_result_container
    search_result_container.empty() #清空本來的container
    final_result_container.empty()
    result=keyword_find(keyword)
    if len(result)==0:
        #print('查無資料')
        search_result_container.error('查無資料', icon="🤖")
    elif len(result)==1:
        #print('只有一筆，直接查類似藥物')
        #直接把一筆的結果丟進去查，並呈現結果
        final_dict=atc_class_med(result.iloc[0,0][:1],result.iloc[0,4],result.iloc[0,0])
        final_result_container.success('相同ATC code品項如下，結果不會顯示查詢藥物', icon="✅")
        final_result_container.header(result.iloc[0,2])
        final_result_container.subheader('學名：'+result.iloc[0,1])
        df_show(final_dict)
        final_result_container.markdown("""---""")
    elif len(result)>1:
        #print('多筆藥物，再做其他選擇')
        #把商品名做成按鈕，學名做成按鈕說明
        result_egname_list=result['商品名'].to_list()
        result_chname_list=result['學名'].to_list()
        search_result_container.info('查詢結果有多項藥品符合，請點選您要查詢的品項', icon="ℹ️") #提示文字
        for i in range(len(result_egname_list)):
            locals()['number'+str(i)] =search_result_container.button(result_egname_list[i],key=i,help=result_chname_list[i],on_click=choose_medication_event,args=(i,))
        search_result_container.markdown("""---""")

def choose_medication_event(args):
    global final_result_container
    final_result_container.empty() #清空本來的container
    final_result_container.success('相同ATC code品項如下，結果不會顯示查詢藥物', icon="✅")
    final_result_container.header(result_egname_list[args])
    result=keyword_find(keyword)
    result=result[args:args+1]
    final_result_container.subheader('學名：'+result.iloc[0,1])
    final_dict=atc_class_med(result.iloc[0,0][:1],result.iloc[0,4],result.iloc[0,0])
    df_show(final_dict)
    final_result_container.markdown("""---""")
    
#全域變數集中區
result_egname_list=list()
#以下開始streamlit語法
st.set_page_config(page_title='替代藥品查詢系統-國軍高雄總醫院左營分院',layout="wide") #修改網頁title，並預設為寬廣模式
st.markdown('## 國軍高雄總醫院左營分院') #用markdown可以讓title變得比較小，比較好看
st.markdown('### 替代藥品查詢系統')

#以下開始功能區
st.write('查詢範圍：醫令碼、中英文商品名、學名')
keyword=st.text_input('請輸入關鍵字')
search_button=st.button('搜尋',type="primary")
st.markdown("""---""")
final_result_container=st.container()
search_result_container=st.container()

st.write('資料庫更新時間：'+open('update_time.txt','r').read())
st.write('Design by 方志文 藥師')
if keyword:
    search_event(keyword)
if search_button:
    search_event(keyword)
