clc
clear all
close all

%% Inputs
P_0 = 0;		%Ambient pressure
P_s_pos = 500;	%Peak peak side on (incident) pressure
n = 10;	%Nr of increments
T_pos = 1; % 50e-3;  %Duration of positive pressure
b = 1.5;    %Parameter in modified Frielander curve

lin = 0;
expon = 1;

%% Calculations
delta_t = T_pos/n;
t = 0.1:delta_t:T_pos;

if lin == 1;
    P = P_0 + P_s_pos*(1-(t/T_pos));
elseif expon == 1;
    P = P_0 + P_s_pos*(1-(t/T_pos)).*exp((-b*t)/(T_pos));
end
%% Plot
plot (t,P)
xlabel('Time [s]')
ylabel('Pressure [Mpa]')

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











