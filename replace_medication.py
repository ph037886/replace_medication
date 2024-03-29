#python 3.10.8 64位元

import streamlit as st
import classification #code來源 https://github.com/topspinj/medcodes
#import googleSheet
import pandas as pd
import datetime
from functools import partial
from deta import Deta

def collect_data(): #把資料抓下來轉dataframe
    #連接資料庫
    deta = Deta(st.secrets['DB_TOKEN'])
    db = deta.Base("replace_medication")
    #把所有資料抓下來
    res = db.fetch()
    all_items = res.items
    while res.last:
        res = db.fetch(last=res.last)
        all_items += res.items
    #抓下來的資料是一個list，裡面有dict，這邊把資料轉成dataframe
    df = pd.DataFrame()
    # 將每個字典加入 DataFrame
    for item in all_items:
        df = df.append(item, ignore_index=True)
    df['time_code'] = pd.to_datetime(df['time_code']) #最後一行是查詢時間，資料庫出來會是str，轉成datetime

def replace_same_form_atc(form, atc, origanal_diacode):
    med_his=pd.read_pickle(r'his_med.pkl')
    med_his=med_his.fillna('') #把空值插入''，避免錯誤
    mask_form=med_his['醫令碼'].str.startswith(form)==True #只查同劑型分類的
    mask_atc=med_his['ATC_CODE'].str.startswith(str(atc))==True #ATC code前幾碼相同
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
    med_his=med_his.fillna('') #把空值插入''，避免錯誤
    mask_diacaode=med_his['醫令碼'].str.upper().str.contains(str(keyword).upper())==True
    mask_chname=med_his['學名'].str.upper().str.contains(str(keyword).upper())==True
    mask_egname=med_his['商品名'].str.upper().str.contains(str(keyword).upper())==True
    mask_cname=med_his['中文名'].str.upper().str.contains(str(keyword).upper())==True
    mask_cname=med_his['中文名'].str.upper().str.contains(str(keyword).upper())==True
    mask_atccode=med_his['ATC_CODE'].str.upper().str.startswith(str(keyword).upper())==True #atc code用startwith，以免查到英文字數字組合在中間相同的
    result=med_his[mask_diacaode | mask_chname | mask_egname | mask_cname | mask_atccode] #用or混合查詢
    return result

def record_to_deta(keyword,origanal_diacode,final_dict):
    def nothing_result(keyword,columns_name):
        _dict={'keyword':[keyword],
               'origanal_diacode':['查無資料']}
        temp=pd.DataFrame.from_dict(_dict)
        temp['time_code']=str(datetime.datetime.now())
        record=pd.DataFrame(columns=columns_name)
        record=pd.concat([record,temp])
        return record
    def success_search(keyword,origanal_diacode,final_dict,columns_name):
        result_list=[keyword,origanal_diacode]
        for key,value in final_dict.items():
            result_list.append(key)
            #result_list.append(len(value['醫令碼'].to_list()))
            value=value[value['DC_TYPE'].str.upper().str.contains('N')==True] #有包含N的代表至少門急住有任意一個地方有開檔
            result_list.append(value['醫令碼'].to_list())
        result_list.append(str(datetime.datetime.now())) #streamlit在伺服器上面，紀錄的時間是格林威治時間，也就是英文倫敦的時間，換成台灣的話要+8
        record=pd.DataFrame([result_list],columns=columns_name)
        return record
    columns_name=['keyword','origanal_diacode','ATC_7','ATC_7R','ATC_5','ATC_5R','ATC_4','ATC_4R','ATC_3','ATC_3R','ATC_1','ATC_1R','time_code']
    if origanal_diacode=='':
        record=nothing_result(keyword,columns_name)
    else:
        record=success_search(keyword,origanal_diacode,final_dict,columns_name)
    record=record.fillna('') #上傳資料有NA可能會出錯
    try: #加入try，如果資料庫出問題，程式功能不會喪失
        #Deta資料庫的連線方式
        deta = Deta(st.secrets['DB_TOKEN'])
        db = deta.Base("replace_medication")
        db.put(record.to_dict('index')[0]) #Deta put資料的方式是用字典
    except:
        pass
    
def df_show(final_dict,eol): #顯示結果的功能
    global search_result_container,final_result_container
    def rating_highlight(val,eol): #pandas填底色功能，比較查詢藥物盈餘比是否比替代藥物低
        try:
            color = 'yellow' if float(val[:-1]) > eol else '' #資料來源的盈餘比已經轉成%格式，type會是str，先把%去除再轉成float
            font_color = 'black' if float(val[:-1]) > eol else '' #字體顏色在瀏覽色設定成黑色模式時，會預設為白色，在螢光底下會不好呈現，這邊將螢光底的自，同步改成黑色，避免狀況
        except:
            color=''
            font_color=''        
        return f'background-color: {color}; color:{font_color}'
    highlight_func = partial(rating_highlight, eol=float(eol[:-1])) #pandas填色用正常的方式不能傳遞參數，使用partial的函式把參數綁進去
    #資料來源是字典
    full_atc=list(final_dict.keys())[0]
    if len(full_atc)==7:
        try:
            atc_df=classification.atc_classification(full_atc)
            atc_df=atc_df.sort_index(ascending=False)
            atc_df=atc_df.fillna('')
            atc_value_list=atc_df['description'].to_list()
        except:
            atc_value_list=['','','','','']
    else:
        atc_value_list=['','','','','']            
    i=0
    for atc, df in final_dict.items():
        df=df[df['DC_TYPE'].str.upper().str.contains('N')==True] #有包含N的代表至少門急住有任意一個地方有開檔
        df=df.drop(columns=['DC_TYPE']) #刪掉不要欄位
        df=df[['醫令碼','商品名','中文名','學名','ATC_CODE','櫃位','盈餘比']]
        final_result_container.header(atc)
        final_result_container.write(atc_value_list[i])
        if df.empty==True:
            final_result_container.warning('本ATC code階層，本院目前無相同ATC code藥品，請找更後面階層藥品', icon="⚠️")
        else:
            final_result_container.info('盈餘比標示黃色，表示該品項盈餘比大於查詢品項')
            final_result_container.dataframe(df.set_index('醫令碼').style.applymap(highlight_func, subset=pd.IndexSlice[:, ['盈餘比']])) 
            #設定醫令碼為index，避免原始index被誤會為存量
            #增加pandas用盈餘比填底色的功能
        i+=1

def mark_dc_medication(result): #如果遇到檔案已鎖檔，在商品名最前面加上已鎖檔
    def apply_dc(row):
        if 'N' not in row['DC_TYPE'].upper():
            row['商品名']='🚫已鎖檔🚫  '+row['商品名']
        return row
    result=result.apply(apply_dc,axis=1)
    return result    

def search_event(keyword):
    global result_egname_list,search_result_container,final_result_container
    search_result_container.empty() #清空本來的container
    final_result_container.empty()
    if keyword=='':
        search_result_container.error('未輸入任何關鍵字', icon="🚨")
    else:
        result=keyword_find(keyword)
        if len(result)==0:
            #print('查無資料')
            search_result_container.error('查無資料', icon="🤖")
            record_to_deta(keyword,'','')
        elif len(result)==1:
            #print('只有一筆，直接查類似藥物')
            #直接把一筆的結果丟進去查，並呈現結果
            result=mark_dc_medication(result)
            final_dict=atc_class_med(result.iloc[0,0][:1],result.iloc[0,4],result.iloc[0,0])
            final_result_container.success('相同ATC code品項如下，結果不會顯示查詢藥物', icon="✅")
            final_result_container.header(result.iloc[0,2])
            final_result_container.subheader('學名：'+result.iloc[0,1])
            final_result_container.subheader('櫃位：'+result.iloc[0,5])
            df_show(final_dict,result.iloc[0,8])
            final_result_container.markdown("""---""")
            record_to_deta(keyword,result.iloc[0,0],final_dict)
        elif len(result)>1:
            #print('多筆藥物，再做其他選擇')
            #把商品名做成按鈕，學名做成按鈕說明
            result=mark_dc_medication(result) #如果遇到檔案已鎖檔，在商品名最前面加上已鎖檔
            result_egname_list=result['商品名'].to_list()
            result_chname_list=result['學名'].to_list()
            search_result_container.info('查詢結果有多項藥品符合，請點選您要查詢的品項', icon="ℹ️") #提示文字
            for i in range(len(result_egname_list)):
                locals()['number'+str(i)] =search_result_container.button(result_egname_list[i],key=i,help=result_chname_list[i],on_click=choose_medication_event,args=(i,))
                #這邊的做法是，因為如果button用不指定變數的方式生成，button內的參數就不能傳遞，所以用local()去生成相同數目的變數
            search_result_container.markdown("""---""")

def choose_medication_event(args):
    global final_result_container
    final_result_container.empty() #清空本來的container
    final_result_container.success('相同ATC code品項如下，結果不會顯示查詢藥物', icon="✅")
    final_result_container.header(result_egname_list[args])
    result=keyword_find(keyword)
    result=result[args:args+1]
    final_result_container.subheader('學名：'+result.iloc[0,1])
    final_result_container.subheader('櫃位：'+result.iloc[0,5])    
    final_dict=atc_class_med(result.iloc[0,0][:1],result.iloc[0,4],result.iloc[0,0])
    df_show(final_dict,result.iloc[0,8])
    final_result_container.markdown("""---""")
    record_to_deta(keyword,result.iloc[0,0],final_dict)
    
#全域變數集中區
result_egname_list=list()
#以下開始streamlit語法
st.set_page_config(page_title='替代藥品查詢系統-國軍左營總醫院',layout="wide") #修改網頁title，並預設為寬廣模式
st.markdown('## 國軍左營總醫院') #用markdown可以讓title變得比較小，比較好看
st.markdown('### 替代藥品查詢系統')

#以下開始功能區
st.write('查詢範圍：醫令碼、中英文商品名、學名、ATC code')
keyword=st.text_input('請輸入關鍵字')
search_button=st.button('搜尋',type="primary")
st.markdown("""---""")
final_result_container=st.container()
search_result_container=st.container()

st.write('品項表資料庫更新時間：'+open('update_time.txt','r').read())
st.write('Design by 臨床藥劑科 方志文 藥師')
if keyword:
    search_event(keyword)
if search_button:
    search_event(keyword)
