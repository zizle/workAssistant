var vm = new Vue({
	el: "#app",
	data:{
		currentDate: "",
		userInfoDict:{},
		title:"",
		mediaOrg:"",
		publishType:"",
		words:"",
		checker:"",
		allowance:"",
		note:"",
		isPartner: false,
		showPartner:false,
		partnerName:'',
		annexFile: "", // 附件
		uploadFileProgress: 0,
	},
	watch:{
		isPartner(){
			if (this.isPartner != 0){this.showPartner = true;}else{this.showPartner = false;this.partnerName=""}
		},
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
		
		
		this.buildDateTime = today + "T00:00";
		this.expireDateTime = today + "T00:00";
		
		
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
		clearInputAfterPostSuccessfully(){
			this.title="";
			this.mediaOrg="";
			this.publishType="";
			this.words="";
			this.checker="";
			this.allowance="";
			this.note="";
			this.isPartner=false;
			this.showPartner=false;
			this.partnerName='';
			this.annexFile=""; // 附件
			var anneEle = document.getElementById('annex');
			anneEle.outerHTML = anneEle.outerHTML;
			this.uploadFileProgress=0;
		},
		// 附件改变
		annexChanged(e){
			this.annexFile=e.target.files[0];
		},
		submitRecord(){
			//console.log('提交');
			// 判断不能为空或默认的字段
			if(
			!this.userInfoDict.uid || 
			!this.title ||
			!this.publishType
			){
				alert("请填写完整信息");
				return;
			}
			if(!this.annexFile){
				if(confirm("确定不上传附件吗?")){
				}else{return;}
			}
			var param = new FormData();
			param.append("custom_time", this.currentDate);
			param.append("org_id", this.userInfoDict.org_id);
			param.append("author_id", this.userInfoDict.uid);
			param.append("title", this.title);
			param.append("work_title", this.workTitle);
			param.append("media_name", this.mediaOrg);
			param.append("rough_type", this.publishType);
			param.append("words", this.words);
			param.append("checker", this.checker);
			param.append("allowance", this.allowance);
			param.append("partner", this.partnerName);
			param.append("note", this.note);
			param.append("annex_file", this.annexFile);
			var request_config = {
				headers:{ "Content-Type": "multipart/form-data"},
				// 上传进度监听
				onUploadProgress: e => {
					var completeProgress = ((e.loaded / e.total * 100) | 0) + "%";
					this.uploadFileProgress = completeProgress;
				}
			};
			
			// 提交数据
			var localThis = this;
			axios.post(host + 'article-publish/',param, request_config)
			.then(function(resp){
				alert(resp.data);
				localThis.clearInputAfterPostSuccessfully();
			})
			.catch(function(e){
				alert(e.response.data);
			})
		},
	}
})