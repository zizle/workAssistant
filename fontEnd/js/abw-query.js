var vm = new Vue({
	el:'#app',
	data:{
		showDoloading: true,
		modifyRid:0,
		modifyingRecord: false,
		showModifyTable: false,
		currentWorks:[],
		modifyWork:{},
		currentTaskType:0,  // 当前的任务类型
		currentPage:1,
		totalPage:1,
		exportDataUrl: ''
	},
	mounted:function(){
		// 请求当前用户的工作情况,以分页的形式
		var localThis = this;
		var hostServer = host + 'abnormal-work/?page=1&pagesize=30&utoken=' + token; 
		axios.get(hostServer)
		.then(function(resp){
			// console.log(resp)
			localThis.currentWorks = resp.data.abworks;
			localThis.currentPage = resp.data.current_page;
			localThis.totalPage = resp.data.total_page;
			localThis.showDoloading = false;
		})
		.catch(function(){localThis.showDoloading = false;})
		
	},
	watch:{
		currentTaskType(newVal, oldVal){
			this.modifyWork.task_type = newVal;
		}
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
		dbclickedRecord(e){
			// 弹窗修改
			// e.target 是当前点击的元素
			// e.currentTarget 是绑定事件的元素
			var rid = e.currentTarget.dataset.rid;
			this.modifyingRecord= true;
			this.showModifyTable=true;
			// console.log(rid);
			// 请求记录
			var server_url = host + 'abnormal-work/' + rid + '/'
			var localThis = this;
			this.modifyRid = rid;
			axios.get(server_url)
			.then(function(resp){
				// console.log(resp.data);
				localThis.modifyWork = resp.data;
				localThis.currentTaskType = resp.data.task_type;
				// localThis.customTime = localThis.modifyWork.custom_time;
			})
			.catch(function(error){
				
			})
			// console.log(e.target.parentElement('tr').dataset.rid)
		},
		closeModify(){
			this.modifyingRecord = false;
			this.showModifyTable=false;
		},
		commitModify(){
			// var modfyData = {
			// 	customTime:this.customTime,
			// 	taskType:this.taskType,
			// 	title:this.title,
			// 	sponsor:this.sponsor,
			// 	appliedOrg:this.appliedOrg,
			// 	applicant:this.applicant,
			// 	link:this.link,
			// 	swissCoin:this.swissCoin,
			// 	note:this.note
			// }
			var modfyData = {
				record_data: this.modifyWork,
				utoken: token
			}
			var localThis = this;
			var server_url = host + 'abnormal-work/' + this.modifyRid + '/'
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
		
		// 刷新当前页
		updateCurrentPage(cPage){
			// 发起请求数据
			this.showDoloading = true;
			var localThis = this;
			var hostServer = host + 'abnormal-work/?page='+ cPage+'&pagesize=30&utoken=' + token; 
			axios.get(hostServer)
			.then(function(resp){
				localThis.currentWorks = resp.data.abworks;
				localThis.currentPage = resp.data.current_page;
				localThis.totalPage = resp.data.total_page;
				localThis.showDoloading = false;
			})
			.catch(function(){localThis.showDoloading = false;})
		},
		exportRecord(){
			this.exportDataUrl = host + 'abnormal-work/export/?utoken=' + token + '&r=' + Math.random();
		},
		
	}
})