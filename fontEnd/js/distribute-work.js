var vm = new Vue({
	el:"#app",
	data:{
		currentUserName:"",
		currentUserFixedCode: "",
		currentUserId: 0,
		worksToDistrubute:[],
	},
	mounted:function(){
		// console.log("请求当前需要的信息,人员信息和模块名称")
		var locationSrcQuery = window.document.location.search.substring(1);
		var vars = locationSrcQuery.split("&");
		var userId = false;
		for (var i=0;i<vars.length;i++){
			var pair = vars[i].split("=");
			if (pair[0] == "uid"){
				userId = pair[1];
			}
		}
		if (!userId){return};
		// 请求信息
		var localThis = this;
		axios.get(host + 'user/' + userId + '/module/')
		.then(function(resp){
			console.log(resp)
			localThis.currentUserId = resp.data.user_id;
			localThis.currentUserName = resp.data.username;
			localThis.currentUserFixedCode = resp.data.fixed_code;
			localThis.worksToDistrubute = resp.data.modules;
		})
		.catch(function(e){
			console.log(e.response.data)
			
		})
		
		
	},
	methods:{
		workStateChanged(e){
			var isWorking = e.target.checked;
			var itemId = e.target.value;
			if (this.currentUserId == 0){return;}
			// 发起改变工作状态的请求
			axios.post(host + 'user/' + this.currentUserId + '/module/' + itemId + '/', data={utoken:token,is_checked:isWorking})
			.then(function(resp){
				console.log(resp)
			})
			.catch(function(e){
				console.log(e.response.data)
			})
			
		}
		
	}
})