var vm = new Vue({
	el: "#app",
	data:{
		varietyInfoDict: {},
		currentDate: "",
		userInfoDict:{},
		variety:"",
		contract:"",
		content:"", // 策略内容
		direction:"",
		hands:"",
		openPosition:"",
		closePosition:"",
		profit:"",
		note:"",
		showContactInput: false,  // 是否显示合约编辑框
	},
	watch:{
		variety(val,oldVal){
			if(!val){
				this.showContactInput = false;
			}else{this.showContactInput = true;}
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
			
		// 请求品种信息
		var localThis = this;
		axios.get(host + 'variety/')
		.then(function(resp){
			localThis.varietyInfoDict = resp.data;
		})
	},
	methods:{
		submitRecord(){
			console.log('提交')
			// 判断不能为空或默认的字段
			if(
			!this.userInfoDict.uid || 
			!this.content ||
			!this.variety ||
			!this.direction
			){
				alert("请填写完整信息");
				return;
			}
			var recordMsg = {
				custom_time:this.currentDate,
				org_id:this.userInfoDict.org_id,
				author_id:this.userInfoDict.uid,
				content:this.content,
				variety:this.variety,
				contract:this.contract,
				direction:this.direction,
				hands: this.hands,
				open_position:this.openPosition,
				close_position:this.closePosition,
				profit:this.profit,
				note:this.note
			};
			console.log(recordMsg)
			// 提交数据
			axios.post(host + 'investrategy/',data=recordMsg)
			.then(function(resp){
				alert(resp.data);
			})
			.catch(function(e){
				alert(e.response.data);
			})
		},
	}
})