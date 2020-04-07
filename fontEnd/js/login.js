var vm = new Vue({
	el: "#app",
	data:{
		showLogin: true,
		// 用户登录
		loginUsername:"", // 登录用户名
		loginUsernameError: "",
		loginPsd:"",  // 登录密码
		loginPsdError: "",
		rememberToken: [],
		loginErrorMsg:"",  // 登录错误提示
		// 部门组织数组
		organizationGroups: [],
		// 绑定注册参数和错误信息提示
		registerName: "", // 注册框的姓名
		registerNameError: "",
		registerPsd1: "", // 注册的密码1
		registerPsd1Error: "",
		registerPsd2: "", // 注册的密码2
		registerPsd2Error: "",
		registerPhone: "", // 注册的手机号
		registerPhoneError: "",
		registerEmail: "", // 注册的邮箱
		registerEmailError: "",
		//orginazationId: 0, // 注册的部门小组
		registerResultMsg: "",
	},
	watch:{
		orginazationId(val, oldVal){
			if(this.orginazationId == 0){
				console.log(val + "===" + oldVal);
				this.orginazationIdError = "请选择部门";
			}
			else{
				this.orginazationIdError = "";
			}
		}
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
		// loginUsername
		loginUsernameFocus(){
			this.loginUsernameError = "";
			this.loginErrorMsg = "";
		},
		loginUsernameBlur(){
			if(!this.loginUsername){
				this.loginUsernameError = "请输入用户名"
			}
		},
		// registerPhoneFocus
		registerPhoneFocus(){
			this.registerPhoneError = "";
		},
		// registerPhoneBlur
		registerPhoneBlur(){
			var phoneReg=/^[1][3,4,5,6,7,8,9][0-9]{9}$/;
			if (!phoneReg.test(this.registerPhone)){
				this.registerPhoneError = "请输入正确的手机号";
			}else{
				this.registerPhoneError = "";
			}
		},
		// registerEmailFocus
		registerEmailFocus(){
			this.registerEmailError = "";
		},
		// registerEmailBlur
		registerEmailBlur(){
			var emailReg = /^([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+@([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+\.[a-zA-Z]{2,3}$/;
			if(!emailReg.test(this.registerEmail)){
				this.registerEmailError = "请输入正确的邮箱";
			}else{
				this.registerEmailError = "";
			}
		},
		//loginPsd
		loginPsdFocus(){
			this.loginPsdError = "";
			this.loginErrorMsg = "";
		},
		loginPsdBlur(){
			if(!this.loginPsd){
				this.loginPsdError = "请输入密码"
			}
		},
		// 点击登录
		userToLogin(){
			if(this.loginUsernameError ||
			!this.loginUsername ||
			this.loginPsdError ||
			!this.loginPsd
			){
				this.loginErrorMsg = "请填写正确用户名密码!";
				return;
			}
			// 发起登录请求
			var remember = this.rememberToken[0];
			if (remember == 1){
				//console.log("记住密码");
			}else{
				remember = 0;
			}
			// 保留this对象
			var localThis = this;
			axios.post(host + "login/",
				data={
					name: this.loginUsername,
					password: md5(this.loginPsd),
					is_remember: parseInt(remember)
				}
			)
			.then(function(resp){
				// console.log(resp);
				localStorage.clear();
				if (remember){
					localStorage.setItem('token', resp.data);
				}
				sessionStorage.clear();
				sessionStorage.setItem('token', resp.data);
				// 跳转到首页面
				window.location.href = "index.html";
			})
			.catch(function(error){
				// console.log(error);
				localThis.loginErrorMsg = error.response.data;
			})
		},
		// 点击注册
		userToRegister(){
			if(this.registerNameError ||
				!this.registerName ||
				this.registerPsd1Error ||
				!this.registerPsd1 ||
				this.registerPsd2Error ||
				!this.registerPsd2||
				!this.registerPhone
				){
				this.registerResultMsg = "请填写正确的信息!";
				return;
			}
			// 组织数据提交注册
			var registerData = {
				name: this.registerName,
				password:  md5(this.registerPsd1),  //  密码md5加密
				organization_id: 1,  // 默认1
				phone: this.registerPhone,
				email: this.registerEmail,
			};
			var localThis = this;
			axios.post(host + "register/",
				data=registerData
			)
			.then(function(resp){
				localThis.registerResultMsg = "信息提交成功^v^";
				//console.log(resp);
			})
			.catch(function(error){
				localThis.registerResultMsg = error.response.data;
				//console.log(error);
			})
		},
	}
	
})