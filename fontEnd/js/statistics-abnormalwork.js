var vm = new Vue({
	el:"#app",
	data:{
		statisticsType:"",
		columns:[],  // 类型必须与返回值一致
		statistics_data: [],  // 类型必须与返回值一致
		// 初始化年份和月份
		year:"",
		month:"",
		
	},
	mounted:function(){
		// 日期默认
		var date = new Date();
		this.year = date.getFullYear()
		this.month = date.getMonth() + 1
		this.getTargetStatistics(this.year, this.month)
	},
	methods:{
		getTargetStatistics(year, month){
			var localThis = this;
			// 获取数据
			axios.get(host + 'statistics/abwork/?year=' + this.year + '&month=' + this.month)
			.then(function(resp){
				// console.log(resp);
				localThis.columns = resp.data.columns;
				localThis.statistics_data = resp.data.data;
			})
			.catch(function(e){
				
			})
		},
		// 点击‘上一月’按钮
		preMonthButtonClicked(){
			if(this.month == 1){
				this.year = this.year - 1;
				this.month = 12;
			}else{
				this.month = this.month - 1;
			}
			// 获取数据
			this.getTargetStatistics(this.year, this.month);
		},
		// 点击下一月
		nextMonthButtonClicked(){
			if(this.month == 12){
				this.year =  this.year + 1;
				this.month = 1;
			}else{
				this.month =  this.month + 1;
			}
			// 获取数据
			this.getTargetStatistics(this.year, this.month);
		}
		
	}
})