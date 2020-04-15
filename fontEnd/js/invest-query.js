var vm = new Vue({
	el:'#app',
	data:{
		showDoloading: true,
		currentRecords:[],
		currentPage:1,
		totalPage:1,
		modifyingRecord: false,
		showModifyTable: false,
		recordToModify:{},
		varietyInfoArray:[],
	},
	mounted:function(){
		this.updateCurrentPage(1);
		// // 请求当前用户的工作情况,以分页的形式
		// var localThis = this;
		// var hostServer = host + 'investment/?page=1&pagesize=30&utoken=' + token; 
		// axios.get(hostServer)
		// .then(function(resp){
		// 	// console.log(resp)
		// 	localThis.currentRecords = resp.data.records;
		// 	localThis.currentPage = resp.data.current_page;
		// 	localThis.totalPage = resp.data.total_page;
		// 	localThis.showDoloading = false;
		// })
		// .catch(function(){localThis.showDoloading = false;})
		//品种
		var localThis = this;
		axios.get(host + 'variety/')
		.then(function(resp){
			localThis.varietyInfoArray = resp.data;
		})
		
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
			var hostServer = host + 'investment/?page='+ requirePage+'&pagesize=30&utoken=' + token; 
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
		closeModify(){
			this.modifyingRecord = false;
			this.showModifyTable=false;
		},
		commitModify(){
			var modfyData = {
				record_data: this.recordToModify,
				utoken: token
			}
			var localThis = this;
			var server_url = host + 'investment/' + this.modifyRid + '/'
			axios.put(server_url, data=modfyData)
			.then(function(resp){
				alert(resp.data);
				localThis.closeModify();
				localThis.updateCurrentPage(localThis.currentPage);
			})
			.catch(function(error){
				alert(error.response.data);
			})
		},
		dbclickedRecord(e){
			// 弹窗修改
			// e.target 是当前点击的元素
			// e.currentTarget 是绑定事件的元素
			var rid = e.currentTarget.dataset.rid;
			this.modifyingRecord= true;
			this.showModifyTable=true;
			// console.log(rid);
			// 请求记录
			var server_url = host + 'investment/' + rid + '/'
			var localThis = this;
			this.modifyRid = rid;
			axios.get(server_url)
			.then(function(resp){
				// console.log(resp.data);
				localThis.recordToModify = resp.data;
				// localThis.customTime = localThis.modifyWork.custom_time;
			})
			.catch(function(error){
				
			})
			// console.log(e.target.parentElement('tr').dataset.rid)
		},
		updateCurrentPage(cPage){
			// 请求当前用户的工作情况,以分页的形式
			var localThis = this;
			var hostServer = host + 'investment/?page='+ cPage +'&pagesize=30&utoken=' + token; 
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
	}
})