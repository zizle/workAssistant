var vm = new Vue({
	el: "#app",
	data:{
		modelFileUrl: host + 'short-message/file/',
		showUploading:false,
		currentDate: "",
		userInfoDict:{},
		variettInfoArray:[],
		content:"",
		messageType:"",
		effectVariety:'',
		note:"",
		showVarietyChecks:false,  // 是否显示品种选择框
		
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
			
		// 请求品种信息
		var localThis = this;
		axios.get(host + 'variety/')
		.then(function(resp){
			localThis.variettInfoArray = resp.data;
		})
		
	},
	
	methods:{
		// 点击品种选框
		selectVariety(){
			this.showVarietyChecks = true;
		},
		// 收起品种选矿
		slideUpVairetyDiv(){
			this.showVarietyChecks = false;
		},
		// 提交记录
		submitRecord(){
			// 判断不能为空或默认的字段
			if(
			!this.userInfoDict.uid || 
			!this.content
			){
				alert("请填写完整信息");
				return;
			}
			var recordMsg = {
				custom_time:this.currentDate,
				org_id:this.userInfoDict.org_id,
				author_id:this.userInfoDict.uid,
				content:this.content,
				msg_type:this.messageType,
				effect_variety:this.effectVariety,
				note:this.note,
			};
			// console.log(recordMsg)
			// 提交数据
			axios.post(host + 'short-message/',data=recordMsg)
			.then(function(resp){
				alert(resp.data);
			})
			.catch(function(e){
				alert(e.response.data);
			})
		},
		// 点击input框就置空value
		clickFileInput(e){
			e.target.value = "";
		},
		UploadDataFile(e){
			this.showUploading = true;
			var param = new FormData();
			param.append("uid", this.userInfoDict.uid);  // 身份验证
			var file = e.target.files[0];
			console.log(file);
			if (typeof(file) == "undefined"){return;}
			param.append("file", file);
			// console.log(param.get('file'));
			var request_config = {
				headers:{ "Content-Type": "multipart/form-data"},
				// 上传进度监听
				onUploadProgress: e => {
					var completeProgress = ((e.loaded / e.total * 100) | 0) + "%";
					this.uploadFileProgress = completeProgress;
				}
			};
			var localThis = this;
			axios.post(host + 'short-message/file/', param, request_config)
			.then(function(resp){
				// console.log(resp);
				localThis.showUploading = false;  // 关闭遮罩
				alert(resp.data);
			})
			.catch(function(e){
				// console.log(e.response.data);
				localThis.showUploading = false;  // 关闭遮罩
				alert(e.response.data)
			})
			
		},
		
	}
})