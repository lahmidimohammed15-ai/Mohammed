
// ============================
// CANVAS
// ============================
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

// ============================
// CONSTANTES
// ============================
const BALL_R = 10;
const FRICTION = 0.985;

// ============================
// SCORE / JOUEURS
// ============================
let score1 = 0;
let score2 = 0;
let currentPlayer = 1;

let playerColors = {
1:null,
2:null
};

// ============================
// ETAT JEU
// ============================
let aiming=false;
let aimX=0;
let aimY=0;
let shotAngle=0;
let power=0;
let ballsMoving=false;

let message="";
let messageTimer=0;
let winner=null;

let gameStarted=false;

// ============================
// SPIN
// ============================
let spinX=0;
let spinY=0;

// ============================
// TROUS
// ============================
const pockets=[
{x:0,y:0,r:24},
{x:canvas.width/2,y:0,r:24},
{x:canvas.width,y:0,r:24},
{x:0,y:canvas.height,r:24},
{x:canvas.width/2,y:canvas.height,r:24},
{x:canvas.width,y:canvas.height,r:24}
];

// ============================
// POSITION BLANCHE
// ============================
const whiteStart={x:200,y:canvas.height/2};

// ============================
// BOULES
// ============================
let balls=[];

function initBalls(){

balls=[];

balls.push({
x:whiteStart.x,
y:whiteStart.y,
dx:0,
dy:0,
r:BALL_R,
color:"white",
type:"white",
active:true
});

const startX=520;
const startY=canvas.height/2;
const space=BALL_R*2+2;

let n=0;

for(let row=0;row<5;row++){
for(let col=0;col<=row;col++){

let color;

if(row===2&&col===1) color="black";
else color=n%2===0?"yellow":"red";

balls.push({
x:startX+row*space,
y:startY-row*space/2+col*space,
dx:0,
dy:0,
r:BALL_R,
color:color,
type:color==="black"?"black":"color",
active:true
});

n++;
}
}

}

initBalls();

// ============================
// TABLE
// ============================
function drawTable(){
ctx.fillStyle="#1b5e20";
ctx.fillRect(0,0,canvas.width,canvas.height);
}

// ============================
// TROUS
// ============================
function drawPockets(){
pockets.forEach(p=>{
ctx.beginPath();
ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
ctx.fillStyle="black";
ctx.fill();
});
}

// ============================
// BOULES
// ============================
function drawBalls(){

balls.forEach(b=>{

if(!b.active) return;

ctx.beginPath();
ctx.arc(b.x,b.y,b.r,0,Math.PI*2);
ctx.fillStyle=b.color;
ctx.fill();

ctx.strokeStyle="black";
ctx.stroke();

});
}

// ============================
// SCORE
// ============================
function drawScore(){

ctx.fillStyle="white";
ctx.font="18px Arial";

ctx.fillText("Joueur 1 : "+score1,20,25);
ctx.fillText("Joueur 2 : "+score2,20,50);

ctx.textAlign="center";
ctx.font="22px Arial";
ctx.fillStyle="yellow";

ctx.fillText("Tour : Joueur "+currentPlayer,canvas.width/2,30);

ctx.textAlign="left";
ctx.fillStyle="white";

if(playerColors[1])
ctx.fillText("Couleur J1 : "+playerColors[1],20,75);

if(playerColors[2])
ctx.fillText("Couleur J2 : "+playerColors[2],20,100);

}

// ============================
// MESSAGE
// ============================
function drawMessage(){

if(messageTimer>0){

ctx.fillStyle="rgba(0,0,0,0.6)";
ctx.fillRect(0,canvas.height/2-40,canvas.width,80);

ctx.fillStyle="white";
ctx.font="30px Arial";
ctx.textAlign="center";
ctx.fillText(message,canvas.width/2,canvas.height/2+10);

messageTimer--;

}
}

// ============================
// VICTOIRE
// ============================
function drawVictory(){

if(!winner) return;

ctx.fillStyle="rgba(0,0,0,0.7)";
ctx.fillRect(0,0,canvas.width,canvas.height);

ctx.fillStyle="gold";
ctx.font="50px Arial";
ctx.textAlign="center";

ctx.fillText("Joueur "+winner+" gagne !",canvas.width/2,canvas.height/2);

}

// ============================
// MENU
// ============================
function drawMenu(){

ctx.fillStyle="rgba(0,0,0,0.7)";
ctx.fillRect(0,0,canvas.width,canvas.height);

ctx.fillStyle="white";
ctx.font="40px Arial";
ctx.textAlign="center";

ctx.fillText("bienvenus dans MDX POOL",canvas.width/2,200);

ctx.font="26px Arial";
ctx.fillText("Clique pour commencer",canvas.width/2,260);

}

// ============================
// TRAJECTOIRE AVEC REBONDS
// ============================
function drawPrediction(){

if(ballsMoving || !gameStarted || winner) return;

const cue = balls[0];

let px = cue.x;
let py = cue.y;

let angle = shotAngle;

let hitBall = null;

// calcul trajectoire
for(let i=0;i<500;i++){

px += Math.cos(angle);
py += Math.sin(angle);

// rebond murs
if(px <= BALL_R || px >= canvas.width-BALL_R){
angle = Math.PI - angle;
}

if(py <= BALL_R || py >= canvas.height-BALL_R){
angle = -angle;
}

// collision bille
for(let j=1;j<balls.length;j++){

const b = balls[j];

if(!b.active) continue;

const d = Math.hypot(px-b.x,py-b.y);

if(d < b.r + cue.r){

hitBall = b;
break;

}

}

if(hitBall) break;

}

// ligne bille blanche
ctx.setLineDash([6,6]);
ctx.beginPath();
ctx.moveTo(cue.x,cue.y);
ctx.lineTo(px,py);
ctx.strokeStyle="white";
ctx.stroke();


// ligne bille touchée
if(hitBall){

const angle2 = Math.atan2(hitBall.y-py, hitBall.x-px);

ctx.beginPath();
ctx.moveTo(hitBall.x,hitBall.y);
ctx.lineTo(
hitBall.x + Math.cos(angle2)*90,
hitBall.y + Math.sin(angle2)*90
);

ctx.strokeStyle="yellow";
ctx.stroke();

}

ctx.setLineDash([]);

}

// ============================
// CANNE
// ============================
function drawCue(){

if(!aiming || ballsMoving) return;

const cue=balls[0];

const offset=power*5;

const sx=cue.x-Math.cos(shotAngle)*(cue.r+offset);
const sy=cue.y-Math.sin(shotAngle)*(cue.r+offset);

const ex=sx-Math.cos(shotAngle)*140;
const ey=sy-Math.sin(shotAngle)*140;

ctx.beginPath();
ctx.moveTo(sx,sy);
ctx.lineTo(ex,ey);

ctx.strokeStyle="#c9a063";
ctx.lineWidth=4;
ctx.stroke();

}

// ============================
// SPIN
// ============================
function drawSpin(){

const cue=balls[0];

ctx.beginPath();
ctx.arc(cue.x,cue.y,20,0,Math.PI*2);
ctx.strokeStyle="white";
ctx.stroke();

ctx.beginPath();
ctx.arc(
cue.x + spinX*10,
cue.y + spinY*10,
4,
0,
Math.PI*2
);

ctx.fillStyle="red";
ctx.fill();

}

// ============================
// COLLISION
// ============================
function resolveCollision(a,b){

const dx=b.x-a.x;
const dy=b.y-a.y;
const dist=Math.hypot(dx,dy);

if(dist===0 || dist>a.r+b.r) return;

const nx=dx/dist;
const ny=dy/dist;

const overlap=(a.r+b.r-dist)/2;

a.x-=nx*overlap;
a.y-=ny*overlap;
b.x+=nx*overlap;
b.y+=ny*overlap;

const p=(a.dx-b.dx)*nx+(a.dy-b.dy)*ny;

a.dx-=p*nx;
a.dy-=p*ny;
b.dx+=p*nx;
b.dy+=p*ny;

}

// ============================
// PHYSIQUE
// ============================
function updateBalls(){

ballsMoving=false;

balls.forEach(b=>{

if(!b.active) return;

b.x+=b.dx;
b.y+=b.dy;

b.dx*=FRICTION;
b.dy*=FRICTION;

if(b.type==="white"){
b.dx+=spinX*0.03;
b.dy+=spinY*0.03;
spinX*=0.98;
spinY*=0.98;
}

if(Math.abs(b.dx)>0.05||Math.abs(b.dy)>0.05){
ballsMoving=true;
}

if(b.x-b.r<0){ b.x=b.r; b.dx*=-1; }
if(b.x+b.r>canvas.width){ b.x=canvas.width-b.r; b.dx*=-1; }
if(b.y-b.r<0){ b.y=b.r; b.dy*=-1; }
if(b.y+b.r>canvas.height){ b.y=canvas.height-b.r; b.dy*=-1; }

pockets.forEach(p=>{

const d=Math.hypot(b.x-p.x,b.y-p.y);

if(d<p.r){

if(b.type==="white"){

message="Faute !";
messageTimer=120;

currentPlayer=currentPlayer===1?2:1;

b.x=whiteStart.x;
b.y=whiteStart.y;
b.dx=0;
b.dy=0;

}
else if(b.type==="black"){

winner=currentPlayer;

}
else{

b.active=false;

if(currentPlayer===1) score1++;
else score2++;

}

}

});

});

for(let i=0;i<balls.length;i++){
for(let j=i+1;j<balls.length;j++){
if(balls[i].active && balls[j].active){
resolveCollision(balls[i],balls[j]);
}
}
}

}

// ============================
// CONTROLES
// ============================
canvas.addEventListener("mousedown",e=>{

if(!gameStarted){
gameStarted=true;
return;
}

if(ballsMoving || winner) return;

const rect=canvas.getBoundingClientRect();

aimX=e.clientX-rect.left;
aimY=e.clientY-rect.top;

const cue=balls[0];

shotAngle=Math.atan2(aimY-cue.y,aimX-cue.x);

aiming=true;

});

canvas.addEventListener("mousemove",e=>{

if(ballsMoving || !gameStarted || winner) return;

const rect=canvas.getBoundingClientRect();

aimX=e.clientX-rect.left;
aimY=e.clientY-rect.top;

const cue=balls[0];

shotAngle=Math.atan2(aimY-cue.y,aimX-cue.x);

if(aiming){
const dist=Math.hypot(aimX-cue.x,aimY-cue.y);
power=Math.min(dist/8,12);
}

});

// Support tactile
canvas.addEventListener("touchstart",e=>{
if(e.touches.length>0){
const rect=canvas.getBoundingClientRect();
aimX=e.touches[0].clientX-rect.left;
aimY=e.touches[0].clientY-rect.top;
const cue=balls[0];
shotAngle=Math.atan2(aimY-cue.y,aimX-cue.x);
if(!gameStarted){ gameStarted=true; return; }
if(ballsMoving || winner) return;
aiming=true;
}
},{passive:false});

canvas.addEventListener("touchmove",e=>{
e.preventDefault();
if(e.touches.length>0 && !ballsMoving && gameStarted && !winner){
const rect=canvas.getBoundingClientRect();
aimX=e.touches[0].clientX-rect.left;
aimY=e.touches[0].clientY-rect.top;
const cue=balls[0];
shotAngle=Math.atan2(aimY-cue.y,aimX-cue.x);
if(aiming){
const dist=Math.hypot(aimX-cue.x,aimY-cue.y);
power=Math.min(dist/8,12);
}
}
},{passive:false});

window.addEventListener("touchend",()=>{
if(aiming && !ballsMoving){
aiming=false;
const cue=balls[0];
cue.dx=Math.cos(shotAngle)*(power||6);
cue.dy=Math.sin(shotAngle)*(power||6);
power=0;
}
});

canvas.addEventListener("mouseup",()=>{

if(ballsMoving) return;

aiming=false;

const cue=balls[0];

cue.dx=Math.cos(shotAngle)*power;
cue.dy=Math.sin(shotAngle)*power;

power=0;

});

// ============================
// RESTART
// ============================
function restartGame(){

score1=0;
score2=0;

playerColors={
1:null,
2:null
};

winner=null;

initBalls();

}

// ============================
// BOUCLE
// ============================
function gameLoop(){

if(!gameStarted){
drawMenu();
requestAnimationFrame(gameLoop);
return;
}

drawTable();
drawPockets();
drawPrediction();
drawCue();
drawSpin();
drawBalls();
drawScore();
drawMessage();
drawVictory();

updateBalls();

requestAnimationFrame(gameLoop);

}

gameLoop();

