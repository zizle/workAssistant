
var vm = new Vue({
	el: "#app",
	data: {
		// 维护一个页面路径数组,用于判断左侧菜单点击后是否有当前的页面路径
		pageUrlArray:[
			'index.html',
			'login.html',
			'org-statistics.html',
			'stuff-work.html',
			'sys-modules.html',
			'abnormal-work.html',
			'abw-query.html',
			'monographic.html',
			'mogp-query.html',
			'investment.html',
			'invest-query.html',
			'investrategy.html',
			'instrategy-query.html',
			'contribute-article.html',
			'contart-query.html'
		],
		showCover:false,
		accessModules:[],
		framePage: "not-found404.html",
	},
	mounted:function(){
		// 请求token登录状态
		// var token = localStorage.getItem('token') || sessionStorage.getItem('token');置于settings.js
		if (!token){
			window.location.href='login.html'
		}
		// 发送token的请求登录状态保持
		var localThis = this;
		axios.get(host + 'login/',{params:{'token':token}})
		.then(function(resp){
			localThis.accessModules = resp.data;
			// console.log(resp.data);
			if (resp.data.length > 0){
				localThis.framePage = resp.data[0].page_url;
			}
		})
		.catch(function(error){
			localStorage.clear();
			sessionStorage.clear();
			window.location.href='login.html'
		})
	},
	// 创建对象之前窗口监听事件(iframe发来的消息事件)
	beforeCreate() {
		// 监听ifram的事件
		var localThis = this;
		window.addEventListener('message', function(e){
			var receiveMsg = e.data;
			if(receiveMsg.name == "showCover"){
				// 显示或关闭覆盖层
				localThis.showCover = receiveMsg.showCover;
			};
			
			if (receiveMsg.name == "modifyModules"){
				// 改变可显模块信息
				localThis.accessModules = receiveMsg.modifyModules;
				
			};
			// 改变frame显示的页面
			if (receiveMsg.name == "changeFramePage"){
				console.log("222" + receiveMsg.changeFramePage + receiveMsg.uid);
				localThis.framePage = receiveMsg.changeFramePage + "?uid=" + receiveMsg.uid;
				document.title = "研究院工作管理系统-工作分配"
			}
			
		})
	},
	methods:{
		// 选择左侧菜单
		selectMenu(e){
			// 处理没有页面的问题
			var page = e.target.dataset.pageurl;
			if (this.pageUrlIsExist(page))
			{
				this.framePage = page;
			}else{
				this.framePage = "not-found404.html";
			}
			document.title = "研究院工作管理系统-" + e.target.innerText
		},
		// 判断数组中是否存在
		pageUrlIsExist(pageUrl){
			var flag = false;
			this.pageUrlArray.forEach(function(item){
				if (item == pageUrl){
					flag = true;
					//break;
				}
			});
			return flag;
		}
	},
})
