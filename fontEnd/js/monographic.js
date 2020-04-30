var vm = new Vue({
	el: "#app",
	data:{
		currentDate: "",
		userInfoDict:{},
		articleTitle:"",
		articleWord:"",
		isOpened: false,
		articleLevel: "",
		articleScore: "",
		isPartner: false,
		showPartner: false,
		partnerName: "",
		note: "",
		annexFile: "", // 附件
		uploadFileProgress: 0,
	},
	watch:{
		isPartner(){
			this.showPartner = this.isPartner;
		}
		
	},
	mounted:function(){
		// 日期默认
		var time = new Date();
		var year = time.getFullYear()
		var month = time.getMonth() + 1
		var date = time.getDate()
		if (month < 10){month = '0' + month;}
		if (date < 10){(date = '0' + date)};
		
		var today = year + '-' + month + '-' + date;
		this.currentDate = today;
		
		// 请求当前用户信息
		if (!token){
				window.location.href='login.html'
			}
			// 发送token的请求登录状态保持
			var localThis = this;
			axios.get(host + 'user/parse-token/?utoken=' + token)
			.then(function(resp){
				localThis.userInfoDict = resp.data;
				// console.log(resp.data);
			})
			.catch(function(e){
				
			})
	},
	methods:{
		// 附件改变
		annexChanged(e){
			this.annexFile=e.target.files[0];
		},
		submitMonograohicRecord(){
			// console.log('提交')
			// 判断不能为空或默认的字段
			if(
			!this.userInfoDict.uid || 
			!this.articleTitle
			){
				alert("请填写完整信息");
				return;
			}
			if(!this.annexFile){
				if(confirm("确定不上传附件吗?")){
				}else{return;}
			}
			var param = new FormData();
			param.append("worker_id", this.userInfoDict.uid);
			param.append("org_id", this.userInfoDict.org_id);
			param.append("work_date", this.currentDate);
			param.append("upload_time", this.currentDate);
			param.append("org_id", this.userInfoDict.org_id);
			param.append("author_id", this.userInfoDict.uid);
			param.append("title", this.articleTitle);
			param.append("words", this.articleWord);
			param.append("is_publish", this.isOpened);
			param.append("level", this.articleLevel);
			param.append("score", this.articleScore);
			param.append("partner_name", this.partnerName);
			param.append("note", this.workNote);
			param.append("annex_file", this.annexFile);
			var request_config = {
				headers:{ "Content-Type": "multipart/form-data"},
				// 上传进度监听
				onUploadProgress: e => {
					var completeProgress = ((e.loaded / e.total * 100) | 0) + "%";
					this.uploadFileProgress = completeProgress;
				}
			};
			// var recordMsg = {
			// 	upload_time:this.currentDate,
			// 	org_id:this.userInfoDict.org_id,
			// 	author_id:this.userInfoDict.uid,
			// 	title:this.articleTitle,
			// 	words:this.articleWord,
			// 	is_publish:this.isOpened,
			// 	level:this.articleLevel,
			// 	score:this.articleScore,
			// 	partner_name:this.partnerName,
			// 	note:this.workNote,
			// };
			// console.log(recordMsg)
			// 提交数据
			axios.post(host + 'monographic/',param, request_config)
			.then(function(resp){
				alert(resp.data);
			})
			.catch(function(e){
				alert(e.response.data);
			})
		},
	}
})