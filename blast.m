clc
clear all
%close all

%% Inputs
P_0 = 0;		%Ambient pressure
P_s_pos = 1.5;	%Peak peak side on (incident) pressure
n = 100;	%Nr of increments
T_pos = 15.6*10^-3; %Duration of positive pressure
b = 8.3;    %Parameter in modified Frielander curve

lin = 0;
expon = 1;

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


% plot(p,model)
% axis([0 max(p) 0 max(model)])
% xlabel('Equivalent plastic strain')
% ylabel('Equivalent stress (in MPa)')




%% Brute force b
clear b
b_list = 0:0.1:20;

int_list = [];
for b = b_list
    P_func = @(time) P_0 + P_s_pos*(1-(time/T_pos)).*exp((-b*time)/(T_pos));
    int = integral(P_func,0,T_pos);
    int_list = [int_list integral(P_func,0,T_pos)];
end

%% Optimize b

i_s = 2.51*10^-3;   %Impulse [MPa*s]

P_func = @(time) P_0 + P_s_pos*(1-(time/T_pos)).*exp((-b*time)/(T_pos));
int = integral(P_func,0,T_pos);

%% section

i_s = 2.51*10^-3;   %Impulse [MPa*s]
syms b
P_func = @(time,b) P_0 + P_s_pos*(1-(time/T_pos)).*exp((-b*time)/(T_pos));
int = integral(P_func,0,T_pos)
eqn = integral(P_func,0,T_pos) == i_s;
sol = solve(eqn,b);

%% 

%fun = @(x) exp(-x.^2).*log(x).^2;
syms x
eqn = sin(x) == 1;
sol = solve(eqn,x)








