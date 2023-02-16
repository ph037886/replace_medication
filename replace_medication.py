#python 3.10.8 64位元

import streamlit as st
import pandas as pd

def replace_same_form_atc(form, atc, origanal_diacode):
    med_his=pd.read_pickle(r'his_med.pkl')
    mask_form=med_his['醫令碼'].str.startswith(form)==True
    mask_atc=med_his['ATC_CODE'].str.contains(str(atc))==True
    without_organal=med_his['醫令碼']!=origanal_diacode
    replace=med_his[mask_atc & mask_form & without_organal]
    return replace

def atc_class_med(form,atc,origanal_diacode):
    class_list=[7,5,4,3,1]
    class_dict=dict()
    for i in class_list:
        atc_slice=atc[:i]
        class_dict[atc_slice]=replace_same_form_atc(form, atc_slice,origanal_diacode)
    return class_dict

def keyword_find(keyword):
    med_his=pd.read_pickle(r'his_med.pkl')
    mask_diacaode=med_his['醫令碼'].str.upper().str.contains(str(keyword).upper())==True
    mask_chname=med_his['學名'].str.upper().str.contains(str(keyword).upper())==True
    mask_egname=med_his['商品名'].str.upper().str.contains(str(keyword).upper())==True
    mask_cname=med_his['中文名'].str.upper().str.contains(str(keyword).upper())==True
    result=med_his[mask_diacaode | mask_chname | mask_egname | mask_cname]
    return result

def search_event(keyword):
    global result_egname_list,search_result_container,final_result_container
    search_result_container.empty()
    final_result_container.empty()
    result=keyword_find(keyword)
    if len(result)==0:
        #print('查無資料')
        search_result_container.write('查無資料')
    elif len(result)==1:
        #print('只有一筆，直接查類似藥物')
        final_dict=atc_class_med(result.iloc[0,0][:1],result.iloc[0,4],result.iloc[0,0])
        for atc, df in final_dict.items():
            final_result_container.header(atc)
            final_result_container.dataframe(df)
        final_result_container.markdown("""---""")
    elif len(result)>1:
        #print('多筆藥物，再做其他選擇')
        #result=result..drop_duplicates(subset=['商品名'])
        result_egname_list=result['商品名'].to_list()
        result_chname_list=result['學名'].to_list()
        #st.button('nothing',on_click=test())
        for i in range(len(result_egname_list)):
            locals()['number'+str(i)] =search_result_container.button(result_egname_list[i],key=i,help=result_chname_list[i],on_click=choose_medication_event,args=(i,))
        search_result_container.markdown("""---""")
        
def choose_medication_event(args):
    global final_result_container
    final_result_container.empty()
    final_result_container.header(result_egname_list[args])
    result=keyword_find(keyword)
    result=result[args:args+1]
    final_dict=atc_class_med(result.iloc[0,0][:1],result.iloc[0,4],result.iloc[0,0])
    for atc, df in final_dict.items():
        final_result_container.subheader(atc)
        final_result_container.dataframe(df)
    final_result_container.markdown("""---""")
    #choose_medication_event(keyword)
    
#全域變數集中區
result_egname_list=list()
#以下開始streamlit語法
st.title('國軍高雄總醫院左營分院')
st.title('替代藥品查詢系統')
#st.write('手機使用，請點選左上角>符號，開啟側邊輸入藥品')
#側欄
#st.title('替代藥品查詢系統')
st.write('查詢範圍：醫令碼、中英文商品名、學名')
keyword=st.text_input('請輸入關鍵字')

search_button=st.button('搜尋',type="primary")
st.markdown("""---""")
search_result_container=st.container()
final_result_container=st.container()
st.write('Design by 方志文 藥師')
if keyword:
    search_event(keyword)
if search_button:
    search_event(keyword)
