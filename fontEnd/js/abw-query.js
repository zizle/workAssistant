var vm = new Vue({
	el:'#app',
	data:{
		currentWorks:[],
		currentPage:1,
		totalPage:1,
	},
	mounted:function(){
		// 请求当前用户的工作情况,以分页的形式
		var localThis = this;
		var hostServer = host + 'abnormal-work/?page=1&pagesize=30&utoken=' + token; 
		axios.get(hostServer)
		.then(function(resp){
			console.log(resp)
			localThis.currentWorks = resp.data.abworks;
			localThis.currentPage = resp.data.current_page;
			localThis.totalPage = resp.data.total_page;
		})
		.catch(function(){})
		
	},
	methods:{
		
	}
})