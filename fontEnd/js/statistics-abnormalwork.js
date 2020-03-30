var vm = new Vue({
	el:"#app",
	data:{
		statisticsType:"",
		stuffs:[],
		statistics_data: {},
		
	},
	mounted:function(){
		var localThis = this;
		// 获取数据
		axios.get(host + 'statistics/abwork/')
		.then(function(resp){
			console.log(resp);
			localThis.stuffs = resp.data.stuffs;
			localThis.statistics_data = resp.data.statistics;
		})
		.catch(function(e){
			
		})
	},
	methods:{
		
	}
})