# 超沙雕迷你网盘，支持文件上传下载删除，压缩包打包解压  
只依赖core python3，现代os开箱即用，页面没有辣鸡js，支持各种命令行浏览器

## 命令行下上传方法
curl -i -X POST -H "Content-Type: multipart/form-data" -F "data=@{filename}" pageurl
