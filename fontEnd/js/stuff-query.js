var vm = new Vue({
		el:"#app",
		data:{
			startDate:'',
			endDate:'',
			stuffs:[],
			workUuid:1,
			currentUserId: 0,
			currentPage: 1,
			totalPage: 1,
			totalCount: 0,
			tableHeaders:[],
			tableRecords:[],
			tableHeaderKeys:[],
			exportDataUrl:'',
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
			this.getStuffs();
		},
		watch:{
			workUuid(){
				this.currentPage = 1;
				this.getTargetPageResults(1);
			}
		},
		methods:{
			getStuffs(){
				var localThis = this;
				axios.get(host + 'users/?utoken=' + token)
				.then(function(resp){
					localThis.stuffs = resp.data;
					// 设置第一个人员选项
					for (var i = 0; i < localThis.stuffs.length; i++) {
						console.log(i);
						if(localThis.stuffs[i].id >1){
							localThis.currentUserId = localThis.stuffs[i].id;
							break;
						}
					}
				})
				.catch(function(error){
					
				})
			},
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
				this.getTargetPageResults(requirePage);
				
			},
			getCurrentOptionsResults(){
				this.getTargetPageResults(1);
			},
			getTargetPageResults(cPage){
				var localThis = this;
				var serverUrl = host + 'statistics/query-stuff/?workuuid=' + this.workUuid + '&userid=' + this.currentUserId + 
				'&startDate=' + this.startDate + '&endDate=' + this.endDate+ '&page='+ cPage+'&pagesize=50' + '&utoken=' + token;
				axios.get(serverUrl)
				.then(function(resp){
					console.log(resp.data);
					localThis.tableHeaderKeys = resp.data.header_keys;
					localThis.tableHeaders = resp.data.table_headers;
					localThis.tableRecords = resp.data.records;
					localThis.totalCount = resp.data.total_count;
					localThis.totalPage = resp.data.total_page;
					localThis.currentPage = resp.data.current_page;
					
				})
				.catch(function(error){
					
				})
			},
			exportRecord(){
				this.exportDataUrl = host  + 'statistics/query-stuff/?workuuid=' + this.workUuid + '&userid=' + this.currentUserId +
				'&startDate=' + this.startDate + '&endDate=' + this.endDate + '&export=1&r=' + Math.random()  + '&utoken=' + token;
			},
			mouseRightClicked(){
				
			},
		},
	})