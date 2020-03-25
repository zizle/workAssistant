var vm = new Vue({
	el:'#app',
	data:{
		showDoloading: true,
		currentRecords:[],
		currentPage:1,
		totalPage:1,
	},
	mounted:function(){
		// 请求当前用户的工作情况,以分页的形式
		var localThis = this;
		var hostServer = host + 'investrategy/?page=1&pagesize=30&utoken=' + token; 
		axios.get(hostServer)
		.then(function(resp){
			// console.log(resp)
			localThis.currentRecords = resp.data.records;
			localThis.currentPage = resp.data.current_page;
			localThis.totalPage = resp.data.total_page;
			localThis.showDoloading = false;
		})
		.catch(function(){localThis.showDoloading = false;})
		
	},
	methods:{
		goToTargetPage(flag){
			console.log(flag);
			var requirePage = this.currentPage;
			// 上一页
			if (flag=="pre"){
				if (this.currentPage == 1){
					console.log('已经是第一页了')
					return;
				}
				requirePage = this.currentPage - 1;
				
			};
			// 下一页
			if(flag=="next"){
				if (this.currentPage >= this.totalPage){
					console.log("已经是最后一页了");
					return;
				}
				requirePage = this.currentPage + 1;
			};
			// 发起请求数据
			this.showDoloading = true;
			var localThis = this;
			var hostServer = host + 'investrategy/?page='+ requirePage+'&pagesize=30&utoken=' + token; 
			axios.get(hostServer)
			.then(function(resp){
				console.log(resp)
				localThis.currentRecords = resp.data.records;
				localThis.currentPage = resp.data.current_page;
				localThis.totalPage = resp.data.total_page;
				localThis.showDoloading = false;
			})
			.catch(function(){localThis.showDoloading = false;})
		},
		
	}
})