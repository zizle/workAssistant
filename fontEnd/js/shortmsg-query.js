var vm = new Vue({
	el:'#app',
	data:{
		showDoloading: true,
		currentRecords:[],
		currentPage:1,
		totalPage:1,
		modifyingRecord: false,
		showModifyTable: false,
		showContextMenu: false,
		recordToModify:{},
		operateRecordId:0,
		exportDataUrl:'',
		startDate:"",
		endDate:"",
		RecordSum:0,
	},
	mounted:function(){
		// 截止日期
		var time = new Date();
		var year = time.getFullYear()
		var month = time.getMonth() + 1
		var date = time.getDate()
		if (month < 10){month = '0' + month;}
		if (date < 10){(date = '0' + date)};
		var today = year + '-' + month + '-' + date;
		this.endDate = today;
		// 起始日期
		this.startDate = "2020-01-01";
		// 请求当前用户的工作情况,以分页的形式
		this.getCurrentOptionsRecords(1);
		
	},
	methods:{
		goToTargetPage(flag){
			// console.log(flag);
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
			this.getCurrentOptionsRecords(requirePage);
		},
		
		getCurrentRecords(){
			this.getCurrentOptionsRecords(1);
		},
		getCurrentOptionsRecords(cPage){
			this.showDoloading = true;
			var localThis = this;
			var hostServer = host + 'short-message/?page='+ cPage+'&pagesize=30'+
			'&startDate=' + this.startDate + '&endDate=' + this.endDate + '&utoken=' + token; 
			axios.get(hostServer)
			.then(function(resp){
				// console.log(resp);
				localThis.currentRecords = resp.data.records;
				localThis.currentPage = resp.data.current_page;
				localThis.totalPage = resp.data.total_page;
				localThis.RecordSum = resp.data.total_count;
				localThis.showDoloading = false;
			})
			.catch(function(){localThis.showDoloading = false;})
		},
		exportRecord(){
			this.exportDataUrl = host + 'short-message/export/?startDate='+ this.startDate +
			'&endDate=' + this.endDate + '&utoken=' + token + '&r=' + Math.random();
		},
		
		closeModify(){
			this.modifyingRecord = false;
			this.showModifyTable=false;
		},
		mouseRightClicked(evt, rid){
			this.operateRecordId = rid;
			var drawing = document.getElementsByClassName('record-table')[0];
			var menu = document.getElementById('contextmenu');
			var rightedge = drawing.clientWidth-evt.clientX;
			var bottomedge = drawing.clientHeight-evt.clientY;
			var scrollLeftPx = document.documentElement.scrollLeft;
			var scrollTopPx = document.documentElement.scrollTop;
			if (rightedge < menu.offsetWidth)               
				menu.style.left = scrollLeftPx + evt.clientX - menu.offsetWidth + "px";            
			else{
				menu.style.left = scrollLeftPx + evt.clientX + "px";
			 }
			if (bottomedge < menu.offsetHeight)
				menu.style.top = scrollTopPx + evt.clientY - menu.offsetHeight + "px";
			else{
				menu.style.top = scrollTopPx + evt.clientY + "px";
			}
			this.showContextMenu = true;
		},
		commitModify(){
			var modfyData = {
				record_data: this.recordToModify,
				utoken: token
			}
			var localThis = this;
			var server_url = host + 'short-message/' + this.operateRecordId + '/'
			axios.put(server_url, data=modfyData)
			.then(function(resp){
				localThis.getCurrentOptionsRecords(localThis.currentPage);
				alert(resp.data);
				localThis.closeModify();
			})
			.catch(function(error){
				alert(error.response.data);
			})
		},
		modifyCurrentRecord(){
			this.showContextMenu = false;
			var recordTable = document.getElementsByClassName('record-table')[0];
			var modifyTable = document.getElementsByClassName('modify-table')[0];
			var coverDiv = document.getElementsByClassName('cover-div')[1];
			var scrollTopPx = document.documentElement.scrollTop;
			modifyTable.style.top = scrollTopPx  + 25 + "px";
			if (document.documentElement.clientHeight < recordTable.clientHeight){
				coverDiv.style.height = recordTable.clientHeight + 40+ "px";
			}
			this.modifyingRecord= true;
			this.showModifyTable=true;
			var server_url = host + 'short-message/' + this.operateRecordId + '/'
			var localThis = this;
			axios.get(server_url)
			.then(function(resp){
				localThis.recordToModify = resp.data;
			})
			.catch(function(error){})
		},
		deleteCurrentRecord(){
			this.showContextMenu = false;
			if(confirm("删除是不可恢复的,您确定要删除吗?")){
				var localThis = this;
				var server_url = host + 'short-message/' + this.operateRecordId + '/?utoken=' + token;
				axios.delete(server_url)
				.then(function(resp){
					localThis.getCurrentOptionsRecords(localThis.currentPage); // 删除完刷新
					alert(resp.data);
				})
				.catch(function(error){
					if (error && error.response)
					{
						alert(error.response.data);
					}
				})
			}
		},
		hideContextMenu(){this.showContextMenu = false;},
		
	}
})