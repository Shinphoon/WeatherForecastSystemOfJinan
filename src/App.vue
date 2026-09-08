<template>

<div class="app">

    <router-view></router-view>


    <div class="bottom-nav">


        <router-link to="/">
            🏠
            <span>首页</span>
        </router-link>


        <router-link to="/reality">
            🌡
            <span>实况</span>
        </router-link>


        <router-link to="/forecast">
            🌤
            <span>预报</span>
        </router-link>


        <router-link to="/mine">
            👤
            <span>我的</span>
        </router-link>


    </div>


</div>

</template>


<style scoped>


.app{

    min-height:100vh;

    padding-bottom:80px;

}


/* 底部导航 */

.bottom-nav{

    position:fixed;

    bottom:0;

    left:50%;

    transform:translateX(-50%);


    width:390px;

    height:70px;


    background:white;


    border-radius:25px 25px 0 0;


    display:flex;

    justify-content:space-around;

    align-items:center;


    box-shadow:0 -3px 15px rgba(0,0,0,0.1);

}



.bottom-nav a{


    text-decoration:none;

    color:#777;


    width:70px;

    height:50px;


    border-radius:15px;


    display:flex;

    flex-direction:column;

    justify-content:center;

    align-items:center;


    font-size:13px;


}



.bottom-nav a.router-link-active{


    background:#e8f1ff;

    color:#267cff;


}



.bottom-nav span{

    margin-top:4px;

}



</style>