clc
clear all
%close all

%%-----------------------------------------------------------------------%%
% Define material constants
%%-----------------------------------------------------------------------%%
rho    = 7.8e-9; %Density
E0     = 210000; %Young's modulus
nu     =    0.3; %Poisson's ratio
sigma0 =    355; %Yield stress
K      =    772; %hardening modulus
n      = 0.1733; %hardening exponent
epspl  =  0.024; %yield plateau strain


%%-----------------------------------------------------------------------%%
% Define element shape
%%-----------------------------------------------------------------------%%
leote = 3.75; %ratio between the in-plane size and the thickness of the shell


%%-----------------------------------------------------------------------%%
% Compute the stress-strain curve
%%-----------------------------------------------------------------------%%
pmax       =  1.0; %maximum plastic strain
npoints    = 1000; %number of points in the stress-strain curve
p          = (0:0.001:1)';
npoints    = npoints+1;
epsp0      = (sigma0/K)^(1/n)-epspl;
model(1,1) = sigma0;
for i=2:npoints
   if p(i) > epspl
      model(i,1) = K*(epsp0+p(i))^n;
   else
      model(i,1) = sigma0;
   end
end


%%-----------------------------------------------------------------------%%
% Compute failure model
%%-----------------------------------------------------------------------%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% define stress triaxiality and Lode parameter
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
T = -0.33:0.01:0.66;
p =  0:0.001:1.0;
for i=1:length(T)
    % lode parameter
    if(T(i)<-0.333)
        L(i) = -3/(9*T(i)^2-1)*(1-sqrt(12*T(i)^2-27*T(i)^4));
    elseif(T(i)<0 && T(i)>=-0.333)
        L(i) =  sqrt(27*T(i)^2/(4-9*T(i)^2));
    elseif(T(i)<0.333 && T(i)>=0)
        L(i) =  -sqrt(27*T(i)^2/(4-9*T(i)^2));
    else
        L(i) = 3/(9*T(i)^2-1)*(1-sqrt(12*T(i)^2-27*T(i)^4));
    end    
end
en  = 2.0*n;
ef  = n+(en-n)/leote;
Wc  = K*(ef)^(n+1)/(n+1);
for i=1:length(T)    
   pf(i) = ((n+1)*Wc/(K*max(0,T(i)+(3-L(i))/(3*sqrt(3+L(i)^2)))))^(1/(n+1));
end
    

%%-----------------------------------------------------------------------%%
% Plot results
%%-----------------------------------------------------------------------%%
figure('Name',num2str(leote),'NumberTitle','off');
subplot(1,2,1)
plot(p,model)
axis([0 max(p) 0 max(model)])
xlabel('Equivalent plastic strain')
ylabel('Equivalent stress (in MPa)')
grid on
subplot(1,2,2)
plot(T,pf)
axis([-0.2 0.67 0 1.0])
xlabel('Stress triaxiality')
ylabel('Equivalent plastic strain')
grid on


%%-----------------------------------------------------------------------%%
% Export material card
%%-----------------------------------------------------------------------%%
fich=fopen(['mat_' num2str(leote) '.inp'],'w');
%fich=fopen(['steelMat.inp'],'w');
% Add material
fprintf(fich,'*Material, name=DOMEX_S355\n');
% Add Density
fprintf(fich,'*Density\n');
fprintf(fich,'%6d\n',rho);
% Add Elasticity
fprintf(fich,'*Elastic\n');
fprintf(fich,'%6d,%6d\n',E0,nu);
% Add plasticity
fprintf(fich,'*Plastic\n');
for i=1:length(p)
    fprintf(fich,'%6d,%6d\n',model(i),p(i));
end
% Add fracture model
fprintf(fich,'*Damage Initiation, criterion=DUCTILE\n');
fprintf(fich,'%6d,%6d\n',1000,-0.67);
for i=1:length(T)
    fprintf(fich,'%6d,%6d\n',pf(i),T(i));
end
fprintf(fich,'*Damage Evolution, type=DISPLACEMENT\n');
fprintf(fich,'%6d,\n',0.001);
% Close file
fclose(fich);
