var tcindex;
//加载层
function tishi2(){
	tcindex = layer.load(0, {shade: [0.2,'#000'],shadeClose:false});
	}
function tishi2close(){
	layer.close(tcindex);
	}	
	
function tishi4(x1,x2){
	$(x2).focus();
	layer.tips(x1, x2, {tips:1});
	//
	}
	
function tishi3(x1){
	layer.alert(x1);
	}	

function tishi1(x1){
	layer.msg(x1, {offset: '50px',shift:6,shade:0});
	}	




function play(y){
	tishi2close();
	if(y=='0x1'){tishi('请输入正确的直推人编号');}
	if(y=='0x2'){tishi('直推人编号不存在.');}
	if(y=='0x12'){tishi('直推人未激活.');}
	if(y=='0x13'){tishi1('直推人被限制使用,详情咨询公司.');}
	if(y=='0x3'){tishi1('请填写您的手机号码');}
	if(y=='0x4'){tishi1('该手机号码已经被注册,请更换别的手机号码');}
	if(y=='0x5'){tishi1('密码格式错误');}
	if(y=='0x6'){tishi1('请输入正确的姓名');}
	if(y=='0x7'){tishi1('请输入安全问题');}
	if(y=='0x8'){tishi1('请输入安全答案');}
	if(y=='0x9'){tishi1('密码格式错误');}
	if(y=='0x10'){tishi1('图片验证码错误');sxyzm();}
	if(y=='0x16'){tishi4('手机验证码错误.请重新输入再试','#x4');}
	if(y=='0x17'){tishi1('您发送手机验证码的频率过高,请稍后再试');}
	if(y=='0x11'){
	layer.open({
		  			content: '您的账户已经注册成功,请牢记您的[玩家编号]和[密码]',
		  			btn: ['OK'],
		  			shadeClose:false,end:function(){
						window.location.href="login.asp";
						}
	 			 });
	}
	if(y=='0x18'){
		 sxyzm();
		 tishi4('短信验证码已经发送到您的手机,请注意查收','#x4');
		 var ccctime=180;
		 $("#getmobyzm").attr({"disabled":"disabled"});
		 var timer = setInterval(function(){
			 //alert(ccctime);
			 $("#getmobyzm").text("验证码已发送 ("+ccctime.toString()+")");
			 ccctime=ccctime-1
			 if(ccctime==0){
				  clearInterval(timer);
				  $("#getmobyzm").removeAttr('disabled');
				  $("#getmobyzm").text('获取短信验证码');
				 }
			 },1000);
		}
	if(y=='0x19'){tishi1("注册失败");}
	

	
	
	if(y=='0x21'){tishi4('账户不存在','#x1');sxyzm();}
	if(y=='0x22'){tishi4('密码错误','#x2');sxyzm();}
	if(y=='0x23'){tishi4('验证码错误','#x3');sxyzm();}
	if(y=='0x24'){tishi3('账户被限制登录');sxyzm();}
	if(y=='0x25'){tishi3('账户未激活,请先联系您的推荐人激活');sxyzm();}
	if(y=='0x29'){window.location.href="index.asp";}
	
	
	
	if(y=='0x31'){tishi4('输入密码','#adminuspwdss');}
	if(y=='0x39'){tishi1("密码修改成功");}
	
	if(y=='0x49'){location.reload();}
	
	
	if(y=='0x71'){tishi4('请输入用户名','#adminus');}
	if(y=='0x72'){tishi4('用户名已经存在','#adminus');}
	if(y=='0x73'){tishi4('输入密码','#adminuspwdss');}
	if(y=='0x79'){window.location.href="users.asp";}	
	
	if(y=='0x98'){tishi3("参数错误");}
	if(y=='0x99'){tishi3("操作频繁！@！");}
	if(y=='0x100'){tishi3("操作成功");}
	if(y=='0x101'){window.location.href="login.asp";}
	

	
}

function sxyzm(){
	$("#yzmpic").attr('src',"../inc/captcha.asp?t="+(new Date().getTime())); 
	}
	
$(function(){
	$(".remain").css('height',($(window).height()-70)+'px');
	
	
	leftmu();
	
	})
	
	
	
function leftmu(){
	//$(selector).toggle(speed,callback);
	$(".left [class='sub-menu']").each(function(){	
		$(this).prev().click(function(e) {
			var zicd=$(this).next(".sub-menu");
			//$(this).next(".sub-menu").toggle(500);
			$(".sub-menu").not(zicd).prev().each(function(){
      			$(this).next(".sub-menu").hide(400);   
				$(this).find(".llong1").removeClass("glyphicon-menu-down");
				$(this).find(".llong1").addClass("glyphicon-menu-left")	;
				})
			if($(zicd).is(":hidden")){
				$(this).find(".llong1").removeClass("glyphicon-menu-left");
				$(this).find(".llong1").addClass("glyphicon-menu-down");
       			$(zicd).show(400);    
			}else{
      			$(zicd).hide(400);   
				$(this).find(".llong1").removeClass("glyphicon-menu-down");
				$(this).find(".llong1").addClass("glyphicon-menu-left");
			}	
        });	
		});
	
	}	
	
function mgo(x){
	var zcd=$("#m"+x.toString());
	var zcc=$(zcd).parent("li").parent(".sub-menu").prev();
	$(zcd).addClass("btn-long32");
	$(zcc).addClass("btn-long16");
	$(zcc).find(".llong1").removeClass("glyphicon-menu-left");
	$(zcc).find(".llong1").addClass("glyphicon-menu-down");
	$(zcd).parent("li").parent(".sub-menu").show();
	//alert($(zcd).parent("li").parent(".sub-menu").prev().html())
	}	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
//验证

//.1验证编号,就是手机号码
function checkMobile(str) { 
	if (checkCnMobile(str) || checkTwMobile(str)) 
	 { return true; }
	 else 
	 { return false; }
	 }
	 
function checkCnMobile(str) { 
	var re = /^1\d{10}$/; 
	if (re.test(str)) 
	 { return true; }
	 else 
	 { return false; }
	 }
	 	 
function checkTwMobile(str) { 
	var re = /^09\d{8}$/; 
	if (re.test(str)) 
	 { return true; }
	 else 
	 { return false; }
	 }	
function checkUser(str){
	var re = /^[a-zA-z]\w{3,15}$/;
	if(re.test(str))
	{ return true; }
	 else 
	 { return false; }
	}
	
	
function checkPwd(str){
	var s=str.length;
	if(s>=6 && s<=30)
	{ return true; }
	 else 
	 { return false; }
	}
	
function checkName(str){
	var s=str.length;
	if(s>=1 && s<=10)
	{ return true; }
	 else 
	 { return false; }
	}	

function checkNum(str) { 
	var re = /^\+?[1-9][0-9]*$/; 
	if (re.test(str)) 
	 { return true; }
	 else 
	 { return false; }
	 }
	 
function checkNum2(str) { 
	var re = /^\+?[1-9][0-9]*$/; 
	if (re.test(str)) 
	 { return true; }
	 else 
	 { return false; }
	 }
function checkNum3(str) { 
	var re = /^\-[1-9][0-9]*$/; 
	if (re.test(str)) 
	 { return true; }
	 else 
	 { return false; }
	 }	 
	 
	 
//判断日期类型是否为YYYY-MM-DD格式的类型    
function IsDate(str){        
    if(str.length!=0){    
        var reg = /^(\d{1,4})(-|\/)(\d{1,2})\2(\d{1,2})$/;     
        var r = str.match(reg);     
        if(r==null)    
            alert('对不起，您输入的日期格式不正确!'); //请将“日期”改成你需要验证的属性名称!    
        }    
}  




/*验证数字：^[0-9]*$ 

验证n位的数字：^\d{n}$  

验证至少n位数字：^\d{n,}$ 

验证m-n位的数字：^\d{m,n}$ 

验证零和非零开头的数字：^(0|[1-9][0-9]*)$ 

验证有两位小数的正实数：^[0-9]+(.[0-9]{2})?$ 

验证有1-3位小数的正实数：^[0-9]+(.[0-9]{1,3})?$ 

验证非零的正整数：^\+?[1-9][0-9]*$ 

验证非零的负整数：^\-[1-9][0-9]*$ 

验证非负整数（正整数 + 0） ^\d+$ 

验证非正整数（负整数 + 0） ^((-\d+)|(0+))$ 

验证长度为3的字符：^.{3}$ 

验证由26个英文字母组成的字符串：^[A-Za-z]+$ 

验证由26个大写英文字母组成的字符串：^[A-Z]+$ 

验证由26个小写英文字母组成的字符串：^[a-z]+$ 

验证由数字和26个英文字母组成的字符串：^[A-Za-z0-9]+$ 

验证由数字、26个英文字母或者下划线组成的字符串：^\w+$ 

验证用户名或昵称经常用到: ^[\u4e00-\u9fa5A-Za-z0-9-_]*$  只能中英文，数字，下划线，减号

验证用户密码:^[a-zA-Z]\w{5,17}$ 正确格式为：以字母开头，长度在6-18之间，只能包含字符、数字和下划线。 

验证是否含有 ^%&',;=?$\" 等字符：[^%&',;=?$\x22]+ 

验证汉字：^[\u4e00-\u9fa5],{0,}$ 

验证Email地址：^\w+[-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$ 

验证InternetURL：^http://([\w-]+\.)+[\w-]+(/[\w-./?%&=]*)?$ ；^[a-zA-z]+://(w+(-w+)*)(.(w+(-w+)*))*(?S*)?$ 

验证电话号码：^(\(\d{3,4}\)|\d{3,4}-)?\d{7,8}$：--正确格式为：XXXX-XXXXXXX，XXXX-XXXXXXXX，XXX-XXXXXXX，XXX-XXXXXXXX，XXXXXXX，XXXXXXXX。 

验证身份证号（15位或18位数字）：^\d{15}|\d{}18$ 

验证一年的12个月：^(0?[1-9]|1[0-2])$ 正确格式为：“01”-“09”和“1”“12” 

验证一个月的31天：^((0?[1-9])|((1|2)[0-9])|30|31)$ 正确格式为：01、09和1、31。 

整数：^-?\d+$ 

非负浮点数（正浮点数 + 0）：^\d+(\.\d+)?$ 

正浮点数 ^(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))$ 

非正浮点数（负浮点数 + 0） ^((-\d+(\.\d+)?)|(0+(\.0+)?))$ 

负浮点数 ^(-(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*)))$ 

浮点数 ^(-?\d+)(\.\d+)?$*/
	