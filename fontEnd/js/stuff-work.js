var vm = new Vue({
	el: "#app",
	data: {
		//workDistributeActive: false,  // 设置人员工作弹窗状态
		ShowcoverDiv: false,
		stuffsArray: [],
		userWorkModuleArray: [],
		//currentOperateUserId: 0,  // 当前操作的用户id
	},
	watch:{
		// 监听工作弹窗弹出状态
		// workDistributeActive(){
		// 	window.parent.postMessage({name: "showCover", showCover: this.workDistributeActive});  // 关闭左遮罩
		// 	console.log(this.workDistributeActive);
		// }
	},
	mounted:function(){
		// 请求所有用户信息
		var localThis = this;
		axios.get(host + 'users/?utoken=' + token)
		.then(function(resp){
			//console.log(resp);
			localThis.stuffsArray = resp.data;
		})
		.catch(function(error){
			//console.log(error.response.data);
		})
	},
	
	methods:{
		// 人员的工作设置
		workDistribute(e){
			var itemid = e.target.value;  // 设置工作的对象id		
			// 让主页跳转页面
			window.parent.postMessage({name:"changeFramePage", changeFramePage: "distribute-work.html", uid:itemid})
		},
		// 重置用户密码
		resetPassword(e){
			var itemid = e.target.value;  // id
			if (confirm("确定重置该用户的密码为:123456吗?")){
				// 请求重置密码
				axios.post(host + "user/" + itemid + "/",
						data={utoken: token, password: md5("123456")}
				)
				.then(function(resp){
					alert(resp.data);
				})
				.catch(function(error){
					if (error.response){
						alert(error.response.data);
					}
				})
			}
		},
	}
})