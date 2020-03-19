var vm = new Vue({
	el: "#app",
	data:{
		showLogin: true,
		usernameError: "",
		psdError: "",
		organizationGroups: [],
		// 绑定注册参数和错误信息提示
		registerName: "", // 注册框的姓名
		registerNameError: "",
		registerPsd1: "", // 注册的密码1
		registerPsd1Error: "",
		registerPsd2: "", // 注册的密码2
		registerPsd2Error: "",
		orginazationId: 0, // 注册的部门小组
		orginazationIdError: "",
	},
	watch:{
	},
	methods:{
		// 点击切换登录与注册框
		toggleLoginRegister(){
			this.showLogin = !this.showLogin;
			if(!this.showLogin  && this.organizationGroups.length <= 0){
				// console.log("现在显示的是注册, 请求系统小组信息");
				var localThis = this;  // 保存this对象,函数内访问不到
				// 请求部门小组信息
				axios.get(host + 'org/')
				.then(function(resp){
					localThis.organizationGroups = resp.data;
					console.log(localThis.organizationGroups)
				})
				.catch(function(error){
					// console.log("请求失败." + error)
					localThis.organizationGroups = [];
				})
			};
		},
		// 鼠标聚焦注册用户名
		registerNameFocus(){
			this.registerNameError = "";
			this.orginazationIdError = "";
		},
		// 注册用户名失去焦点
		registerNameBlur(){
			if(!this.registerName){
				this.registerNameError = "请输入用户名";
			}
		},
		// registerPsd1Focus
		registerPsd1Focus(){
			this.registerPsd1Error = "";
			this.orginazationIdError = "";
		},
		// registerPsd1Blur
		registerPsd1Blur(){
			var reg = /^[a-zA-Z0-9_]{6,20}$/;
			if(!reg.test(this.registerPsd1)){
				this.registerPsd1Error = "密码需为大小写字母,下划线组成6-20位字符";
			}
		},
		// registerPsd2Focus
		registerPsd2Focus(){
			this.registerPsd2Error = "";
			this.orginazationIdError = "";
		},
		// registerPsd2Blur
		registerPsd2Blur(){
			if (this.registerPsd1 != this.registerPsd2){
				this.registerPsd2Error = "两次输入密码不一致.";
			}
		},
		
		// 点击登录
		userToLogin(){
			this.psdError = "密码错误";
		},
		// 点击注册
		userToRegister(){
			if(this.registerNameError ||
				!this.registerName ||
				this.registerPsd1Error ||
				!this.registerPsd1 ||
				this.registerPsd2Error ||
				!this.registerPsd2 ||
				this.orginazationIdError ||
				this.orginazationId == 0){
				this.orginazationIdError = "请填写正确的信息!";
				return;
			}
			// 组织数据提交注册
			var registerData = {
				name: this.registerName,
				password: this.registerPsd1,
				orginazation_id: this.orginazationId,
			};
			axios.post(host + "register/")
			.then(function(resp){
				console.log(resp);
			})
			.catch(function(error){
				console.log(error);
			})
				console.log(registerData);
		},
	}
	
})