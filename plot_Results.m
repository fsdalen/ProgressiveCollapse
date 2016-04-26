clear all; close all; clc; 

files = dir('*.txt');
n = size(files,1);
legendPlot = [];

for i  = 1:n
    Name = char(files(i).name);
    t = findstr( 'Time', Name);
    f = findstr('Force', Name);
    d = findstr('Displ', Name);
    pre = findstr('_', Name);
    Pre = files(i).name(1:pre(1) - 1);
%Lag liste med prefikser
    if i == 1
        Ppre(i) = cellstr(Pre);
        temp = 0;
    end
    l = length(Ppre);
    for j = 1:l     
        temp = findstr(Pre, char(Ppre(j)));
        temp = sum(temp);
    end
    if temp == 0
        Ppre(l+1) = cellstr(Pre);
    end
    temp = 0;
%Lag variabler
    if t > 0
        fileID = fopen(files(i).name,'r');
        T = fscanf(fileID,'%f');
        eval([Pre '_Time = T;']);
        fclose(fileID);
    end
    if f > 0
        fileID = fopen(files(i).name,'r');
        if sum(findstr('kN', Name)) > 0
                F = fscanf(fileID,'%f');
        else
                F = fscanf(fileID,'%f')/1000;
        end
        eval([Pre '_Force = F;']);
        fclose(fileID);
    end
    if d > 0
        fileID = fopen(files(i).name,'r');
        D = fscanf(fileID,'%f');
        if sum(D) < 0
            D = -D;
        end
        eval([Pre '_Displ = D;']);
        fclose(fileID);
    end
end


%lag figur
NoPlots = length(Ppre);
colors = distinguishable_colors(NoPlots);

figure(1)
ax = gca;
ax.FontSize = 12;       %Changes font size of the axes (default = 10). Legend font size is by default 90% of axes
set(gca,'DefaultLineLineWidth',1)  %Change line width. Default = 0.5

hold on
for i = 1:NoPlots
    disp = eval([char(Ppre(i)) '_Displ']);
    force = eval([char(Ppre(i)) '_Force']);
    h = plot(disp,force,'color',colors(i,:));
    eval(['h' num2str(i) ' = h;'])                           %Number the handle, e.g. h1
    eval(['legendPlot(' num2str(i) ') = h' num2str(i) ';']) %Put the handle into the legendPlot vector, which we will later relate lengendText
end
grid on
xlabel('Displacement [mm]')
ylabel('Force [kN]')
legend(legendPlot,Ppre)
