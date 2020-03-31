var vm = new Vue({
	el: "#app",
	data:{
		stuffsArray:[],
		organizations:{},
		
	},
	mounted: function() {
		// 请求所有用户信息
		var localThis = this;
		axios.get(host + 'users/?utoken=' + token)
		.then(function(resp){
			console.log(resp);
			localThis.stuffsArray = resp.data;
		})
		.catch(function(error){
			//console.log(error.response.data);
		})
		
		// 请求部门小组信息
		axios.get(host + 'org/')
		.then(function(resp){
			localThis.organizations = resp.data;
		})
		.catch(function(e){
			
		})
		
	},
	methods:{
		// 审核用户
		userActiveChanged(e){
			// 获取select
			var selectElement = e.target.parentElement.previousElementSibling.firstChild;
			var sIndex = selectElement.selectedIndex
			// 获取select选中的值
			var orgId = selectElement[sIndex].value;
			// 发送审核请求
			var itemid = e.target.value;
			var isChecked = e.target.checked;
			// 请求后端修改
			axios.put(host + 'user/' + itemid + '/',
				data={
					org_id: orgId,
					is_checked: isChecked,
					utoken: token,
				})
				.then(function(resp){
					console.log(resp);
					// alert(resp.data);
				})
				.catch(function(error){
					alert(error.response.data);
					//console.log(error)
				})
		},
	}
})