%% Plot curves

%{
This takes multiple files and plots the data

FileName: xyData_header_curveName.txt
    curveName: Name of curve
    header: what is plotted, currently ignored


File should be tabular delimided with with two columns
First row is ignored as headers.
Legend is created from curveName
X and Y labels are manual at the end of the script
%}

%% Perliminaries

close all;

clear all; 
clc; 


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
plotName = 'together';

%Modify apparance of plot
fontSize =  16;   %Font width of axis, legend 90%, axis title 110% of this
linWidth =  1.2;     
figSize =  [700 700];   %[width height]
xLimit = [0.0 11.0];      %comment out gives auto
yLimit = [0.0 3.5];   %comment out gives auto
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%




%% Read files

%Get files
files = dir('xyData*');
n = size(files,1);


%Read files into data
for i = 1:n
    %Read tab file
    structure = tdfread(files(i).name);
    
    %Get model name
    name = files(i).name;
    underscores = strfind(name, '_');
    dot = strfind(name, '.');
    data(i).name = name(underscores(2)+1:dot-1);
    

    %Get variables
    field = fieldnames(structure);
  
    underscore = strfind(field(1),'_');
    name1 = char(field(1));
    data(i).x = eval(['structure.' name1]);
    
    underscore = strfind(field(2),'_');
    name2 = char(field(2));
    data(i).y = eval(['structure.' name2]);
    
    %Shift curves to start at 0,0
    %This removes all the first 0,0 exept one
%     nonZero = find(data(i).y);
%     firstNonZero = nonZero(1);
%     data(i).y = data(i).y(firstNonZero-1:end);
%     data(i).x = data(i).x(1:end-(firstNonZero-2));

    %Change units in order force, disp and energies together
    fileName = files(i).name;
    underscores = strfind(fileName, '_');
    data(i).var = fileName(underscores(1)+1:underscores(2)-1);
    if strfind(data(i).var, 'R2')
        data(i).y = data(i).y*0.66*10^-7; %Normalize force
    elseif strfind(data(i).var, 'U2')
        data(i).y = data(i).y*-10^-2; %Convert displacement to positive decimeter
    elseif strfind(data(i).var, 'Work')
        data(i).y = data(i).y*10^-8; %Convert from mJ 10^5 J
    elseif strfind(data(i).var, 'Energy')
        data(i).y = data(i).y*10^-8; %Convert from mJ 10^5 J
    end
    
end

%Get axis titles from last file
xLabel = 'Time [s]';
yLabel = ' ';

%% Plot

colors = distinguishable_colors(n);
legendPlot = [];


hFig = figure('Name',plotName,'NumberTitle','off');
hFig.Position = [200 200 figSize];
hFig.PaperUnits = 'points';
hFig.PaperSize = figSize;
hFig.PaperPositionMode = 'auto';
hFig.PaperPosition = [0 0 figSize];

fig = gca;   %current figure handle
fig.FontSize = fontSize;       
set(fig,'DefaultLineLineWidth',linWidth)




hold on
for i = 1:n
    h = plot(data(i).x, data(i).y ,'color' ,colors(i,:));
    eval(['h' num2str(i) ' = h;'])                           %Number the handle, e.g. h1
    eval(['legendPlot(' num2str(i) ') = h' num2str(i) ';']) %Put the handle into the legendPlot vector, which we will later relate lengendText
end

grid on
xlabel(xLabel)
ylabel(yLabel)

%Create legend
for i = 1:n
    if strfind(data(i).var, 'R2')
        data(i).name=strcat(data(i).var,' [ ]');
    elseif strfind(data(i).var, 'U2')
        data(i).name=strcat(data(i).var,' [10^{-1} m]');
    elseif strfind(data(i).var, 'Work')
        data(i).name=strcat(data(i).var,' [10^5 J]');
    elseif strfind(data(i).var, 'Energy')
        data(i).name=strcat(data(i).var,' [10^5 J]');
    end
end

legend(legendPlot,data.name,'location','best');

%Change limits
if exist('xLimit');
    xlim(xLimit);
end

if exist('yLimit');
    ylim(yLimit);
end

print(plotName, '-dpdf')
