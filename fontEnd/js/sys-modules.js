var vm = new Vue({
	el: "#app",
	data: {
		// 是否显示遮罩层
		showCover:false,
		// 是否显示新增弹窗
		addModuleActive: false,
		newModuleName:"", // 新的模块名称绑定
		newModulePageUrl: "", // 新模块页面路径
		newModuleParentId: 0, // 新模块的父级
		modulesArray: [],  // 当前所有功能模块数组[{},{}]
	},
	
	mounted:function(){
		// 请求系统模块
		var localThis = this;
		axios.get(host + 'module/')
		.then(function(resp){
			// console.log(resp.data);
			localThis.modulesArray = resp.data;
		})
		.catch(function(){
			
		})
	},
	methods:{
		// 点击新增模块按钮
		addNewModule(){
			// 像主页面发送消息,显示左侧遮罩
			window.parent.postMessage({name: "showCover", showCover: 1});
			// 显示本页面遮罩
			this.showCover = true;
			// 显示弹窗
			this.addModuleActive = true;
		},
		// 关闭新增模块弹窗
		closeNewModulePopup(){
			this.addModuleActive = false;  // 关闭弹窗
			this.showCover = false;  // 关闭本页遮罩
			window.parent.postMessage({name: "showCover", showCover: 0});  // 关闭左遮罩
		},
		// 提交新模块
		submitNewModule(){
			if (!this.newModuleName){
				alert("请填写名称!");
				return;
			}
			if(this.newModuleParentId && !this.newModulePageUrl){
				alert("子级功能模块请填写页面路径.")
				return;
			}
			// 提交
			var localThis = this;
			axios.post(host + 'module/',
			data={
				module_name: this.newModuleName,
				page_url:this.newModulePageUrl,
				parent_id:this.newModuleParentId,
				utoken: token,
			})
			.then(function(resp){
				// 关闭遮罩
				localThis.closeNewModulePopup();
				localThis.modulesArray = resp.data; // 修改变量
				window.parent.postMessage({name: "modifyModules", modifyModules: resp.data});
				
			})
			.catch(function(error){
				alert("添加错误了:" + error.response.data);
			})
			
		},
		// 复选框改变
		checkBoxChanged(e){
			//console.log(e);
			var itemid = e.target.value;
			var optaction = e.target.dataset.action;
			var isChecked = e.target.checked;
			console.log(itemid, optaction)
			// 请求后端修改
			axios.put(host + 'module/' + itemid + '/',
			 data={
				operation: optaction,
				is_checked: isChecked,
				utoken: token,
			})
			.then(function(resp){
				// console.log(resp);
				// alert(resp.data);
			})
			.catch(function(error){
				console.log(error)
			})
		}
	}
	
})