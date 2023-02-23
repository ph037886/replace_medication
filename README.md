# replace_medication

更新日誌：
2023-02-20 新增查詢結果記錄在資料庫功能，使用deta資料庫，record_to_deta()

---

鑒於近期 (2023-02-15)缺藥問題嚴重，長期被問有甚麼替代品項可以使用，單純靠醫院的藥物辨識系統執行起來略微複雜，設計可以查詢替代藥品的程式

本程式有串接streamlit，https://ph037886-replace-medication-replace-medication-oykc19.streamlit.app/

## 程式流程
1. 抓取系統所有曾經有的藥物，無論是否還在使用，製成藥品資料庫，並產生檔案更新日期
2. 混合查詢醫令碼、中文商品名、英文商品名、學名，查詢院內是否曾經有此藥物，有的話將這些藥物列出來，製成streamlit的按鈕。(keyword_find())
3. 點選後，會將被選擇的藥品的Atc code，一層一層拆開，並與資料庫內的資料比較，將每一層的Atc code當key，搜尋出來的df當value。atc_class_med()
4. 查詢出來的結果，紀錄查詢關鍵字，每一層的ATC code，替代的藥物ACT code的list。df轉dict，配合deta的傳輸方式
5. 呈現在streamlit上
6. 後續只需定期將檔案更新到github上面即可

## 待解問題
主要都是介面問題，對streamlit尚不熟悉，很多功能都還不會用  
1. 按鈕的排列，不太確定能不能向右5個再往下，這樣會比較不會哪麼長
2. 本來的規劃是按鈕按完後，在最下面才出現表格，但是因為如果查詢結果太多，按鈕會疊很多，使用體驗就會不好，只能先改這樣
3. 重複查詢有些東西會重複empty()的作用沒有出來

## 移轉方式
基本上全台都在缺藥，所以如果其他醫院有需要可以直接clone過去  
1. his_med.pkl是資料來源  
可以改成Excel或csv來源，對資料量小的檔案能不會差太多，還是建議用csv  
如果真的不會用python，整個clone過去，直接再github上面改也可以  
更改方式，把所有的pd.read_pickle(r'his_med.pkl')改成  
csv->```pd.read_csv(r'his_med.csv')```  
xlsx->```pd.read_excel(r'his_med.xlsx')```  
xls不要用，那樣連requirements.txt要裝別的套件上去，會操作這個得大概也會用pickle  
2. his_med欄位 '醫令碼','學名','商品名','中文名','ATC_CODE','櫃位','DC_TYPE'  
不要改欄位名稱，這個很麻煩，可以的話連順序也不要改  
3. DC_TYPE欄位有點反邏輯，因為本院註記方式，N是未鎖檔  
所以N是藥品可以繼續用，有點反邏輯  
本院有三個庫，門 急 住，分開的，所以分三個鎖檔，這邊我的邏輯是把三個串一起，如果有一個是N就視為還再用  
不過這部分不影響使用，因為搜尋邏輯裡面是用contains，也就是有任何一個有N就可以，所以如果自己使用要改成Y N各一個也沒差  
4. 其他部分就是註冊streamlit與串接github  
主要是參考這篇 https://ithelp.ithome.com.tw/articles/10298666  
比較不一樣的地方是requirements.txt，一開始用conda或pip匯出，都會出錯，後來接用pip install的方法做，就很簡單了，當正常方式安裝  
5. Deta資料庫連結方式用try去做，即使沒有使用deta也不影響使用  