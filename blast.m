clc
clear all
%close all

%% Inputs
P_0 = 0;		%Ambient pressure
P_s_pos = 1.5;	%Peak peak side on (incident) pressure
n = 100;	%Nr of increments
T_pos = 15.6*10^-3; %Duration of positive pressure
i_s = 2.51*10^-3;   %Impulse

lin = 0;
expon = 1;


%% Solve for b
syms b
p_int = @(b) ((P_s_pos*T_pos)/b^2)*(b-1+exp(-b));
%p_int = @(b) ((P_s_pos*T_pos)/2)*(exp(-b/T_pos));
eqn = p_int(b) == i_s;
b = double(solve(eqn,b));


%Double check soultion
% P_func = @(t) P_0 + P_s_pos*(1-(t/T_pos)).*exp((-b*t)/(T_pos));
% int = integral(P_func,0,T_pos);

%% Calculations
delta_t = T_pos/n;
t = 0:delta_t:T_pos;

if lin == 1;
    P = P_0 + P_s_pos*(1-(t/T_pos));
elseif expon == 1;
    P = P_0 + P_s_pos*(1-(t/T_pos)).*exp((-b*t)/(T_pos));
end

%Shift the graph 1 time step to the right in order to start at 0,0
t = [t T_pos+delta_t];
P = [0 P];

%% Plot
plot (t,P)
xlabel('Time [s]')
ylabel('Pressure [Mpa]')
%axis([0 max(p) 0 max(model)])

%% Wrtie to file
fich=fopen(['blast.csv'],'w');
%fprintf(fich, 'Time [s] Pressure [MPa]\n');
for i=1:length(P)
    fprintf(fich,'%6d\t%6d\n',t(i),P(i));
end
fclose(fich);

%% Functions that don't work

% %% Optimize b
% 
% i_s = 2.51*10^-3;   %Impulse [MPa*s]
% 
% P_func = @(time) P_0 + P_s_pos*(1-(time/T_pos)).*exp((-b*time)/(T_pos));
% int = integral(P_func,0,T_pos);
% 
% 
% %% Brute force b
% clear b
% b_list = 0:0.1:20;
% 
% int_list = [];
% for b = b_list
%     P_func = @(time) P_0 + P_s_pos*(1-(time/T_pos)).*exp((-b*time)/(T_pos));
%     int = integral(P_func,0,T_pos);
%     int_list = [int_list integral(P_func,0,T_pos)];
% end
% %% section
% 
% i_s = 2.51*10^-3;   %Impulse [MPa*s]
% syms b
% P_func = @(time) P_0 + P_s_pos*(1-(time/T_pos)).*exp((-b*time)/(T_pos));
% int =@(b) integral(P_func,0,T_pos);
% eqn = int(b) == i_s;
% sol2 = solve(eqn,b);
% 
% %% Analytical in MATLAB
% P_func = @(t,p) P_0 + P_s_pos*(1-(t/T_pos)).*exp((-b*t)/(T_pos));
% 
% syms p t
% sol3 = solve(int(P_func,t,0,T_pos)==i_s, p);
% solve(
% int(
% %% 
% 
% %fun = @(x) exp(-x.^2).*log(x).^2;
% syms x
% eqn = sin(x) == 1;
% sol = solve(eqn,x)
% 
% 
% 
% 




