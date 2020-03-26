var vm = new Vue({
	el: "#app",
	data:{
		currentDate: "",
		userInfoDict:{},
		varietyInfoDict:{},
		content:"",
		messageType:"",
		effectVariety:[],
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
			localThis.varietyInfoDict = resp.data;
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
			console.log(recordMsg)
			// 提交数据
			axios.post(host + 'short-message/',data=recordMsg)
			.then(function(resp){
				alert(resp.data);
			})
			.catch(function(e){
				alert(e.response.data);
			})
			
			
		},
		
	}
})