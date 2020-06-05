var vm = new Vue({
	el:"#app",
	data:{
		userCenterMenus:['基础信息', '修改密码'],
	},
	methods:{
		selectUserCenterMenu(e){
			var text = e.target.innerText;
			var iframe = document.getElementById("userIframe");
			if (text=="基础信息"){
				iframe.src="baseInfo.html";
			}else if (text == "修改密码"){
				iframe.src="modifyPsd.html";
			}
			
		},
	}
	
})