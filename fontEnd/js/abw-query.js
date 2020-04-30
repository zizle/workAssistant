var vm = new Vue({
	el:'#app',
	data:{
		showDoloading: true,
		modifyingRecord: false,
		showModifyTable: false,
		showContextMenu: false,
		currentWorks:[],
		modifyWork:{},
		currentTaskType:0,  // 当前的任务类型
		currentPage:1,
		totalPage:1,
		exportDataUrl: '',
		operateRecordId:0,
		annexFile: "", // 新的附件
		startDate:"",
		endDate:"",
		RecordSum: 0,
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
	watch:{
		currentTaskType(newVal, oldVal){
			this.modifyWork.task_type = newVal;
		}
	},
	
	methods:{
		// 选择了新附件
		annexChanged(e){
			this.annexFile=e.target.files[0];
		},
		// 前往页
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
			this.getCurrentOptionsRecords(requirePage);
			
		},
		// 查询当前数据
		getCurrentRecords(){
			this.getCurrentOptionsRecords(1);
		},
		// 获取当前配置条件数据
		getCurrentOptionsRecords(cPage){
			this.showDoloading = true;
			var localThis = this;
			var hostServer = host + 'abnormal-work/?page='+ cPage+'&pagesize=30'+
			'&startDate=' + this.startDate + '&endDate=' + this.endDate + '&utoken=' + token; 
			axios.get(hostServer)
			.then(function(resp){
				// console.log(resp);
				localThis.currentWorks = resp.data.abworks;
				localThis.currentPage = resp.data.current_page;
				localThis.totalPage = resp.data.total_page;
				localThis.RecordSum = resp.data.total_count;
				localThis.showDoloading = false;
			})
			.catch(function(){localThis.showDoloading = false;})
		},
		exportRecord(){
			this.exportDataUrl = host + 'abnormal-work/export/?startDate='+ this.startDate +
			'&endDate=' + this.endDate + '&utoken=' + token + '&r=' + Math.random();
		},
		// 右击显示菜单
		mouseRightClicked(evt, rid){
			this.operateRecordId = rid;
			var drawing = document.getElementsByClassName('record-table')[0];
			var menu = document.getElementById('contextmenu');
			// 获取当前鼠标右键按下后的位置，据此定义菜单显示的位置
			var rightedge = drawing.clientWidth-evt.clientX;
			var bottomedge = drawing.clientHeight-evt.clientY;
			var scrollLeftPx = document.documentElement.scrollLeft;
			var scrollTopPx = document.documentElement.scrollTop;
			// 如果从鼠标位置到容器右边的空间小于菜单的宽度，就定位菜单的左坐标（Left）为当前鼠标位置向左一个菜单宽度
			if (rightedge < menu.offsetWidth)               
				//menu.style.left = drawing.scrollLeft + evt.clientX - menu.offsetWidth + "px";
				menu.style.left = scrollLeftPx + evt.clientX - menu.offsetWidth + "px";
			else{
			//否则，就定位菜单的左坐标为当前鼠标位置
				menu.style.left = scrollLeftPx + evt.clientX + "px";
			 }
			//如果从鼠标位置到容器下边的空间小于菜单的高度，就定位菜单的上坐标（Top）为当前鼠标位置向上一个菜单高度
			if (bottomedge < menu.offsetHeight)
				//menu.style.top = drawing.scrollTop + evt.clientY - menu.offsetHeight + "px";
				menu.style.top = scrollTopPx + evt.clientY - menu.offsetHeight + "px";
			else{
			//否则，就定位菜单的上坐标为当前鼠标位置
				menu.style.top = scrollTopPx + evt.clientY + "px";
			}
			this.showContextMenu = true;
		},
		
		// 右键选择编辑
		modifyClickedRecord(){
			this.showContextMenu = false;
			// 改变覆盖框的的高度并将编辑界面移动至当前界面
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
			// console.log(rid);
			// 请求记录
			var server_url = host + 'abnormal-work/' + this.operateRecordId + '/'
			var localThis = this;
			axios.get(server_url)
			.then(function(resp){
				// console.log(resp.data);
				localThis.modifyWork = resp.data;
				localThis.currentTaskType = resp.data.task_type;
				// localThis.customTime = localThis.modifyWork.custom_time;
			})
			.catch(function(error){
				
			})
		},
		// 关闭修改框
		closeModify(){
			this.modifyingRecord = false;
			this.showModifyTable=false;
			var annexInput = document.getElementById('annexFile');
			annexInput.value='';
			this.annexFile = '';
		},
		// 提交修改
		commitModify(){
			var param = new FormData();
			for (var key in this.modifyWork){
				param.append(key, this.modifyWork[key])
			}
			param.append("annex_file", this.annexFile);
			param.append('utoken', token);
			var request_config = {
				headers:{ "Content-Type": "multipart/form-data"},
				// // 上传进度监听
				// onUploadProgress: e => {
				// 	var completeProgress = ((e.loaded / e.total * 100) | 0) + "%";
				// 	this.uploadFileProgress = completeProgress;
				// }
			};
			
			
			// var modfyData = {
			// 	record_data: this.modifyWork,
			// 	utoken: token
			// }
			var localThis = this;
			var server_url = host + 'abnormal-work/' + this.operateRecordId + '/';
			axios.put(server_url, param, request_config)
			.then(function(resp){
				localThis.getCurrentOptionsRecords(localThis.currentPage); // 修改完刷新
				alert(resp.data);
				localThis.closeModify();
			})
			.catch(function(error){
				alert(error.response.data);
			})
		},
		// 删除当前记录
		deleteCurrentRecord(){
			this.showContextMenu = false;
			if(confirm("删除是不可恢复的,您确定要删除吗?")){
				var localThis = this;
				var server_url = host + 'abnormal-work/' + this.operateRecordId + '/?utoken=' + token;
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
		hideContextMenu(){
			this.showContextMenu = false;
		},
	}
})
