var vm = new Vue({
	el: "#app",
	data: {
		// 动态绑定菜单被点了的样式
		isMenuActive: 0,
		accessModules:[],
		framePage: "stuff-maintain.html",
	},
	beforeMount:function(){
		// 请求token登录状态
		var token = localStorage.getItem('token') || sessionStorage.getItem('token');
		if (!token){
			window.location.href='login.html'
		}
		// 发送token的请求登录状态保持
		var localThis = this;
		axios.get(host + 'login/',{params:{'token':token}})
		.then(function(resp){
			//console.log(resp.data);
			localThis.accessModules = resp.data;
		})
		.catch(function(error){
			localStorage.clear();
			sessionStorage.clear();
			window.location.href='login.html'
		})
	},
	methods:{
		// 选择左侧菜单
		selectMenu(e,index){
			this.framePage = e.target.dataset.pageurl;
			document.title = "研究院工作管理系统-" + e.target.innerText
			this.isMenuActive = index;
		}
	},
	
})