
var vm = new Vue({
	el: "#app",
	data: {
		// 维护一个页面路径数组,用于判断左侧菜单点击后是否有当前的页面路径
		pageUrlArray:[
			'index.html',
			'login.html',
			'org-statistics.html',
			'stuff-work.html',
			'stuff-auditing.html',
			'sys-modules.html',
			'variety-manager.html',
			'abnormal-work.html',
			'abw-query.html',
			'monographic.html',
			'mogp-query.html',
			'investment.html',
			'invest-query.html',
			'investrategy.html',
			'instrategy-query.html',
			'contribute-article.html',
			'contart-query.html',
			'short-message.html',
			'shortmsg-query.html',
			'ondutymsg.html',
			'ondutymsg-query.html',
			'statistics-abnormalwork.html',
			'statistics-monographic.html',
			'statistics-investment.html',
			'statistics-investrategy.html',
			'statistics-contributearticle.html',
			'statistics-shortmessage.html',
			'statistics-onduty.html',
			'statistics-query.html'
		],
		showCover:false,
		accessModules:[],
		framePage: "default-indexpage.html",
	},
	mounted:function(){
		// 请求token登录状态
		// var token = localStorage.getItem('token') || sessionStorage.getItem('token');置于settings.js
		if (!token){
			window.location.href='login.html'
		}
		// 发送token的请求登录状态保持
		var localThis = this;
		axios.get(host + 'login/',{params:{'token':token}, timeout:3000})
		.then(function(resp){
			localThis.accessModules = resp.data;
			if(resp.data.length <= 0)
			{
				alert('系统暂不可用...');
				window.location.href='login.html'
			}
			// console.log(resp.data);
			// if (resp.data.length > 0){
			// 	localThis.framePage = resp.data[0].page_url;
			// }
		})
		.catch(function(error){
			if (error && error.response){
			localStorage.clear();
			sessionStorage.clear();
			}
			else{alert("连接服务器失败...")}
			window.location.href='login.html';
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
				// 改变可显示模块信息的数组pageUrlArray
				localThis.accessModules = receiveMsg.modifyModules;
			};
			// 改变frame显示的页面
			if (receiveMsg.name == "changeFramePage"){
				// console.log("222" + receiveMsg.changeFramePage + receiveMsg.uid);
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
			var flag = this.pageUrlIsExist(page);
			if (flag)
			{
				// console.log(page);
				// this.framePage = page;
				var iframeEle = document.getElementById("rightframe");
				iframeEle.src=page;
				
			}else{
				this.framePage = "not-found404.html";
			}
			document.title = "研究院工作管理系统-" + e.target.innerText;
			
		},
		// 判断数组中是否存在
		pageUrlIsExist(pageUrl){
			for (var i = 0; i < this.pageUrlArray.length; i++) {
				if(this.pageUrlArray[i] == pageUrl){
					return true;
				}
			}
			return false;
		}
	},
})
