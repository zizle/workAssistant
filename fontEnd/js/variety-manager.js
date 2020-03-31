var vm = new Vue({
	el:"#app",
	data:{
		showCover: false,
		addVarietyActive: false,  // 是否显示新增弹窗
		newVarietyName: "",
		newVarietyEnCode:"",
		newVarietyParentId:0,
		varietyArray:[], // 所有品种
	},
	mounted: function(){
		// 请求所有品种
		var localThis = this;
		axios.get(host + 'variety/')
		.then(function(resp){
			console.log(resp.data);
			localThis.varietyArray = resp.data;
		})
		.catch(function(){})
	},
	methods:{
		addNewVariety(){
			// 像主页面发送消息,显示左侧遮罩
			window.parent.postMessage({name: "showCover", showCover: 1});
			// 显示本页面遮罩
			this.showCover = true;
			// 显示弹窗
			this.addVarietyActive = true;
		},
			
		closeNewVarietyPopup(){
			this.addVarietyActive = false;  // 关闭弹窗
			this.showCover = false;  // 关闭本页遮罩
			window.parent.postMessage({name: "showCover", showCover: 0});  // 关闭左遮罩
		},
		submitNewVariety(){
			if (!this.newVarietyName){
				alert("请填写名称!");
				return;
			}
			// 提交
			var localThis = this;
			axios.post(host + 'variety/',
			data={
				variety_name: this.newVarietyName,
				parent_id:this.newVarietyParentId,
				en_code: this.newVarietyEnCode,
				utoken: token,
			})
			.then(function(resp){
				// 关闭遮罩
				localThis.closeNewVarietyPopup();
				localThis.varietyArray = resp.data; // 修改变量	
			})
			.catch(function(error){
				alert("添加错误了:" + error.response.data);
			})
		},
		checkBoxChanged(){
			
		},
	}
})