var vm = new Vue({
	el:'#app',
	data:{
		showDoloading: true,
		currentRecords:[],
		currentPage:1,
		totalPage:1,
		exportDataUrl: '',
		modifyingRecord: false,
		showModifyTable: false,
		recordToModify:{},
	},
	mounted:function(){
		// 请求当前用户的专题研究数据,以分页的形式
		var localThis = this;
		var hostServer = host + 'monographic/?page=1&pagesize=30&utoken=' + token; 
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
			this.updateCurrentPage(this.currentPage);
		},
		exportRecord(){
			this.exportDataUrl = host + 'monographic/export/?utoken=' + token + '&r='+  Math.random();
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
			var server_url = host + 'monographic/' + this.modifyRid + '/'
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
			var server_url = host + 'monographic/' + rid + '/'
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
			// 发起请求数据
			this.showDoloading = true;
			var localThis = this;
			var hostServer = host + 'monographic/?page='+ cPage+'&pagesize=30&utoken=' + token; 
			axios.get(hostServer)
			.then(function(resp){
				localThis.currentRecords = resp.data.records;
				localThis.currentPage = resp.data.current_page;
				localThis.totalPage = resp.data.total_page;
				localThis.showDoloading = false;
			})
			.catch(function(){localThis.showDoloading = false;})
		},
	}
})