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
		submitRecord(){
			console.log('提交');
			// 判断不能为空或默认的字段
			if(
			!this.userInfoDict.uid || 
			!this.title
			){
				alert("请填写完整信息");
				return;
			}
			var recordMsg = {
				custom_time:this.currentDate,
				org_id:this.userInfoDict.org_id,
				author_id:this.userInfoDict.uid,
				title: this.title,
				media_name: this.mediaOrg,
				rough_type:this.publishType,
				words: this.words,
				checker:this.checker,
				allowance:this.allowance,
				note:this.note
			};
			// console.log(recordMsg)
			// 提交数据
			axios.post(host + 'article-publish/',data=recordMsg)
			.then(function(resp){
				alert(resp.data);
			})
			.catch(function(e){
				alert(e.response.data);
			})
		},
	}
})