var vm = new Vue({
	el:"#app",
	data:{
		showUploading:false,
		taskTypes:{},  // 初始化的任务类型
		selectedTaskType:0,  // 选择的任务类型
		currentDate:"",  // 当前时间
		userInfoDict: {}, // 用户信息
		isPartner: false, // 任务是否是合作完成的标识
		showPartner: false,  // 是否显示键入合作者
		partnerName: "", // 协作者
		workTitle: "", // 主题/标题
		sponser:"",//主办方
		applicantOrg: "", //申请部门/受用单
		applicationPerson: "",//申请者
		linkNumber: "", // 联系电话
		ruiBiCount:"", // 瑞币情况
		incomeAllowance: "", // 收入补贴
		workNote: "",// 备注
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
		// 工作类型选择
		var localThis = this;
		axios.get(host + 'nonormal-work/task-type/')
		.then(function(resp){
			//console.log(resp.data);
			localThis.taskTypes = resp.data;
		})
		.catch(function(){});
		
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
		// 提交后清空数据
		clearInputAfterPostSuccessfully(){
			this.selectedTaskType=0; // 选择的任务类型
			this.isPartner=false; // 任务是否是合作完成的标识
			this.showPartner=false;  // 是否显示键入合作者
			this.partnerName=""; // 协作者
			this.workTitle=""; // 主题/标题
			this.sponser="";//主办方
			this.applicantOrg=""; //申请部门/受用单
			this.applicationPerson="";//申请者
			this.linkNumber=""; // 联系电话
			this.ruiBiCount=""; // 瑞币情况
			this.incomeAllowance=""; // 收入补贴
			this.workNote="";// 备注
			this.annexFile=""; // 附件
			var annexEle = document.getElementById('annex');
			annexEle.outerHTML = annexEle.outerHTML;
			this.uploadFileProgress=0;
		},
		// 附件改变
		annexChanged(e){
            console.log(this.annexFile);
			this.annexFile=e.target.files[0];
            console.log(this.annexFile);
		},
		// 提交任务
		submitWorkRecord(){
			// console.log(this.annexFile);
			// 判断不能为或默认的字段
			if(
			!this.userInfoDict.uid || 
			!this.selectedTaskType ||
			!this.workTitle
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
			param.append("task_type", this.selectedTaskType);
			param.append("work_title", this.workTitle);
			param.append("sponsor", this.sponser);
			param.append("applicat_org", this.applicantOrg);
			param.append("application_person", this.applicationPerson);
			param.append("link_number", this.linkNumber);
			param.append("ruibi_count", this.ruiBiCount);
			param.append("income_allowance", this.incomeAllowance);
			param.append("partner_name", this.partnerName);
			param.append("work_note", this.workNote);
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
			axios.post(host + 'abnormal-work/',param, request_config)
			.then(function(resp){
				alert(resp.data);
				localThis.clearInputAfterPostSuccessfully(); // 清空数据
			})
			.catch(function(e){
				console.log('错误');
				alert(e.response.data);
			})
			
		},
		clickFileInput(e){
			e.target.value = "";
		},
		// 批量上传
		UploadDataFile(e){
			this.showUploading = true;
			var param = new FormData();
			param.append("uid", this.userInfoDict.uid);  // 身份验证
			var file = e.target.files[0];
			param.append("file", file);
			// console.log(param.get('file'));
			if (typeof(file)=="undefined"){return;}
			var request_config = {
				headers:{ "Content-Type": "multipart/form-data"},
				// 上传进度监听
				onUploadProgress: e => {
					var completeProgress = ((e.loaded / e.total * 100) | 0) + "%";
					this.uploadFileProgress = completeProgress;
				}
			};
			var localThis = this;
			axios.post(host + 'abnormal-work/file/', param, request_config)
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