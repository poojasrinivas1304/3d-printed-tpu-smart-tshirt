%% make_median_curves_subjects_1_2_3.m
% Median-curve visualizations for Subject 1, Subject 2, and Subject 3.
%
% This script creates two outputs:
%
% 1) figure7b_position_median_profile_curves
%    - One subplot per sensor.
%    - X-axis = posture/position 1 to 8.
%    - Y-axis = subject-level median DeltaR/R0.
%    - Thin gray lines = each subject.
%    - Thick black line = median across subjects.
%    - This uses the same scalar median values used for Figure 7 ANOVA.
%
% 2) figure7c_repetition_aligned_median_curves
%    - Repetition-aligned median waveforms.
%    - For selected sensors, each posture panel shows the pointwise median
%      curve across repeated hold segments, with an interquartile band.
%    - This is useful as a supplementary figure to show the repeated-trial
%      waveform shape rather than only one scalar median.
%
% Normalization:
%   R0 = median resistance during first baselineSec seconds.
%   DeltaR/R0 = (R - R0) / R0.
%
% Notes:
%   - The paper's Figure 7 used one median value per subject-position-sensor.
%   - The repetition-aligned curves are an additional visualization, not the
%     direct input to one-way ANOVA.

clear; close all; clc;

%% ---------------- USER SETTINGS ----------------
scriptPath = mfilename('fullpath');
if isempty(scriptPath)
    error('Run this file as a saved script so repository paths can be resolved.');
end
scriptDir = fileparts(scriptPath);
repoRoot = fileparts(fileparts(scriptDir));
dataDir = fullfile(repoRoot, 'data', 'processed');

files = {'subject_01.csv','subject_02.csv','subject_03.csv'};
subjectLabels = {'Subject 1','Subject 2','Subject 3'};

nSensors = 10;
positions = 1:8;
baselineSec = 2;
useHoldOnly = true;
removeQCSamples = true;

outDir = fullfile(repoRoot, 'results', 'analysis');
if exist(outDir, 'dir') ~= 7
    mkdir(outDir);
end

% Figure 7b: median profile curves across positions.
makePositionMedianProfileFigure = true;

% Figure 7c: repetition-aligned median waveform curves.
makeRepetitionAlignedCurvesFigure = true;
selectedSensorsForRepetitionCurves = [2 3 8];
nGrid = 101;               % normalized hold-time grid: 0 to 100%
minSegmentSamples = 20;    % discard very short hold fragments
showIQRBand = true;
showIndividualSegments = false;  % set true only for debugging; can look busy

% Plot/export style.
exportResolution = 600;
fontColor = [0 0 0];
axisFontSize = 7.0;
labelFontSize = 8.0;
titleFontSize = 8.5;
mainTitleFontSize = 14;
subjectLineColor = [0.68 0.68 0.68];
medianLineColor = [0 0 0];
iqrColor = [0.82 0.82 0.82];
zeroLineColor = [0.45 0.45 0.45];

%% ---------------- LOAD AND NORMALIZE DATA ----------------
D = cell(numel(files),1);

for subjIdx = 1:numel(files)
    D{subjIdx} = loadSubjectNormalized(fullfile(dataDir, files{subjIdx}), ...
        baselineSec, nSensors, removeQCSamples);
end

%% ---------------- COMPUTE SCALAR MEDIANS FOR FIGURE 7B ----------------
medianVals = nan(numel(files), numel(positions), nSensors);
medianRows = [];
rowCounter = 0;

for subjIdx = 1:numel(files)
    t = D{subjIdx}.t; %#ok<NASGU>
    pos = D{subjIdx}.position;
    holdMask = D{subjIdx}.is_hold == 1;
    Y = D{subjIdx}.dr;

    if ~useHoldOnly
        holdMask = true(size(holdMask));
    end

    for s = 1:nSensors
        y = Y(:,s);
        for pIdx = 1:numel(positions)
            p = positions(pIdx);
            mask = holdMask & pos == p & isfinite(y);
            val = localNanMedian(y(mask));
            medianVals(subjIdx,pIdx,s) = val;

            rowCounter = rowCounter + 1;
            medianRows(rowCounter).Subject = string(subjectLabels{subjIdx}); %#ok<SAGROW>
            medianRows(rowCounter).SubjectIndex = subjIdx; %#ok<SAGROW>
            medianRows(rowCounter).Sensor = s; %#ok<SAGROW>
            medianRows(rowCounter).Position = p; %#ok<SAGROW>
            medianRows(rowCounter).MedianDeltaR_R0 = val; %#ok<SAGROW>
            medianRows(rowCounter).NSamples = nnz(mask); %#ok<SAGROW>
        end
    end
end

medianTable = struct2table(medianRows);
writetable(medianTable, fullfile(outDir, 'median_curves_subject_position_medians.csv'));

%% ---------------- ANOVA P-VALUES FOR TITLES ----------------
pValues = nan(nSensors,1);
for s = 1:nSensors
    yAll = [];
    groupAll = [];
    for pIdx = 1:numel(positions)
        vals = medianVals(:,pIdx,s);
        vals = vals(isfinite(vals));
        yAll = [yAll; vals(:)]; %#ok<AGROW>
        groupAll = [groupAll; positions(pIdx)*ones(numel(vals),1)]; %#ok<AGROW>
    end
    [~, pValues(s)] = anovaOneWayManual(yAll, groupAll);
end

anovaTable = table((1:nSensors)', pValues, ...
    'VariableNames', {'Sensor','p_ANOVA'});
writetable(anovaTable, fullfile(outDir, 'median_curves_anova_pvalues.csv'));

%% ---------------- FIGURE 7B: POSITION MEDIAN PROFILE CURVES ------------
if makePositionMedianProfileFigure

    fig = figure('Color','w', 'Units','centimeters', 'Position',[2 2 27 15.5]);
    try
        set(fig, 'Renderer', 'painters');
        set(fig, 'InvertHardcopy', 'off');
    catch
    end

    tl = tiledlayout(2,5, 'Padding','compact', 'TileSpacing','compact');
    title(tl, 'Median normalized sensor-response profiles across positions', ...
        'FontWeight','bold', 'FontSize', mainTitleFontSize, 'Color', fontColor);

    markerList = {'o','s','^'};

    for s = 1:nSensors
        ax = nexttile(tl, s);
        hold(ax,'on');

        vals = squeeze(medianVals(:,:,s)); % subjects x positions
        yForLimits = vals(:);
        setDisplayYLimits(ax, yForLimits, true, 0.16);
        addZeroReferenceLine(ax, zeroLineColor);

        % IQR band across subjects.
        q25 = nan(1,numel(positions));
        q50 = nan(1,numel(positions));
        q75 = nan(1,numel(positions));
        for pIdx = 1:numel(positions)
            v = vals(:,pIdx);
            q25(pIdx) = localPercentile(v,25);
            q50(pIdx) = localPercentile(v,50);
            q75(pIdx) = localPercentile(v,75);
        end

        patch(ax, [positions fliplr(positions)], [q25 fliplr(q75)], iqrColor, ...
            'EdgeColor','none', 'FaceAlpha',0.40, 'HandleVisibility','off');

        % Individual subject profiles.
        hSubj = gobjects(numel(files),1);
        for subjIdx = 1:numel(files)
            hSubj(subjIdx) = plot(ax, positions, vals(subjIdx,:), '-', ...
                'Color', subjectLineColor, 'LineWidth',0.70, ...
                'Marker', markerList{1+mod(subjIdx-1,numel(markerList))}, ...
                'MarkerSize',3.2, 'MarkerFaceColor','w', ...
                'MarkerEdgeColor', [0.35 0.35 0.35]);
        end

        % Group median across subjects.
        hMed = plot(ax, positions, q50, '-o', ...
            'Color', medianLineColor, 'LineWidth',1.45, ...
            'MarkerSize',3.8, 'MarkerFaceColor',medianLineColor, ...
            'MarkerEdgeColor',medianLineColor);

        title(ax, sprintf('S%d\n%s', s, formatPValue(pValues(s))), ...
            'FontSize', titleFontSize, 'FontWeight','normal', 'Color', fontColor);

        xlim(ax, [0.5 8.5]);
        xticks(ax, positions);

        if s > 5
            xlabel(ax, 'Position', 'FontSize', labelFontSize, 'Color', fontColor);
        else
            set(ax, 'XTickLabel', []);
        end

        if s == 1 || s == 6
            ylabel(ax, 'Median \DeltaR/R_0', 'Interpreter','tex', ...
                'FontSize', labelFontSize, 'Color', fontColor);
        end

        formatAxis(ax, axisFontSize, fontColor);

        if s == 1
            legend([hSubj; hMed], [subjectLabels {'Group median'}], ...
                'Location','best', 'FontSize',6.3, 'TextColor',fontColor, 'Box','off');
        end
    end

    outBase = fullfile(outDir, 'figure7b_position_median_profile_curves');
    exportFigureSet(fig, outBase, exportResolution);
end

%% ---------------- FIGURE 7C: REPETITION-ALIGNED MEDIAN CURVES ----------
if makeRepetitionAlignedCurvesFigure

    holdGrid = linspace(0,1,nGrid);
    allCurves = cell(nSensors, numel(positions));
    curveRows = [];
    curveRowCounter = 0;

    % Extract all contiguous hold segments, align each to 0-100% hold time,
    % and store an interpolated curve.
    for subjIdx = 1:numel(files)
        t = D{subjIdx}.t;
        pos = D{subjIdx}.position;
        holdMask = D{subjIdx}.is_hold == 1;
        Y = D{subjIdx}.dr;

        for s = selectedSensorsForRepetitionCurves
            y = Y(:,s);
            for pIdx = 1:numel(positions)
                p = positions(pIdx);

                mask = holdMask & pos == p & isfinite(y) & isfinite(t);
                segments = contiguousSegments(find(mask));

                for segIdx = 1:numel(segments)
                    idx = segments{segIdx};
                    if numel(idx) < minSegmentSamples
                        continue;
                    end

                    tt = t(idx);
                    yy = y(idx);

                    good = isfinite(tt) & isfinite(yy);
                    tt = tt(good);
                    yy = yy(good);

                    if numel(tt) < minSegmentSamples || max(tt) <= min(tt)
                        continue;
                    end

                    xNorm = (tt - tt(1)) ./ (tt(end) - tt(1));
                    [xUnique, uniqueIdx] = unique(xNorm, 'stable');
                    yUnique = yy(uniqueIdx);

                    if numel(xUnique) < 3
                        continue;
                    end

                    yInterp = interp1(xUnique, yUnique, holdGrid, 'linear', 'extrap');
                    allCurves{s,pIdx} = [allCurves{s,pIdx}; yInterp]; %#ok<AGROW>

                    curveRowCounter = curveRowCounter + 1;
                    curveRows(curveRowCounter).Subject = string(subjectLabels{subjIdx}); %#ok<SAGROW>
                    curveRows(curveRowCounter).SubjectIndex = subjIdx; %#ok<SAGROW>
                    curveRows(curveRowCounter).Sensor = s; %#ok<SAGROW>
                    curveRows(curveRowCounter).Position = p; %#ok<SAGROW>
                    curveRows(curveRowCounter).SegmentIndexWithinSubject = segIdx; %#ok<SAGROW>
                    curveRows(curveRowCounter).Duration_s = tt(end) - tt(1); %#ok<SAGROW>
                    curveRows(curveRowCounter).NSamples = numel(tt); %#ok<SAGROW>
                end
            end
        end
    end

    if ~isempty(curveRows)
        curveSummaryTable = struct2table(curveRows);
        writetable(curveSummaryTable, fullfile(outDir, 'median_curves_repetition_segment_summary.csv'));
    end

    % Save the computed curves as a MAT file for reuse.
    save(fullfile(outDir, 'median_curves_repetition_aligned_data.mat'), ...
        'allCurves', 'holdGrid', 'selectedSensorsForRepetitionCurves', 'positions');

    fig = figure('Color','w', 'Units','centimeters', 'Position',[1 1 30 18]);
    try
        set(fig, 'Renderer', 'painters');
        set(fig, 'InvertHardcopy', 'off');
    catch
    end

    nRows = numel(selectedSensorsForRepetitionCurves);
    nCols = numel(positions);
    tl = tiledlayout(nRows, nCols, 'Padding','compact', 'TileSpacing','compact');
    title(tl, 'Repetition-aligned median hold curves', ...
        'FontWeight','bold', 'FontSize', mainTitleFontSize, 'Color', fontColor);

    for r = 1:nRows
        s = selectedSensorsForRepetitionCurves(r);
        for pIdx = 1:numel(positions)
            p = positions(pIdx);
            ax = nexttile(tl, (r-1)*nCols + pIdx);
            hold(ax,'on');

            curves = allCurves{s,pIdx};

            if isempty(curves)
                title(ax, sprintf('P%d (n=0)', p), 'FontSize', titleFontSize, ...
                    'FontWeight','normal', 'Color', fontColor);
                formatAxis(ax, axisFontSize, fontColor);
                continue;
            end

            q25 = nan(1,nGrid);
            q50 = nan(1,nGrid);
            q75 = nan(1,nGrid);
            for k = 1:nGrid
                q25(k) = localPercentile(curves(:,k),25);
                q50(k) = localPercentile(curves(:,k),50);
                q75(k) = localPercentile(curves(:,k),75);
            end

            yForLimits = curves(:);
            setDisplayYLimits(ax, yForLimits, true, 0.12);
            addZeroReferenceLine(ax, zeroLineColor);

            xPct = 100*holdGrid;

            if showIndividualSegments
                plot(ax, xPct, curves', '-', 'Color', [0.80 0.80 0.80], ...
                    'LineWidth',0.35, 'HandleVisibility','off');
            end

            if showIQRBand
                patch(ax, [xPct fliplr(xPct)], [q25 fliplr(q75)], iqrColor, ...
                    'EdgeColor','none', 'FaceAlpha',0.45, 'HandleVisibility','off');
            end

            plot(ax, xPct, q50, '-', 'Color', medianLineColor, ...
                'LineWidth',1.25, 'HandleVisibility','off');

            if r == 1
                title(ax, sprintf('P%d (n=%d)', p, size(curves,1)), ...
                    'FontSize', titleFontSize, 'FontWeight','normal', 'Color', fontColor);
            end

            if pIdx == 1
                ylabel(ax, sprintf('S%d\n\DeltaR/R_0', s), ...
                    'Interpreter','tex', 'FontSize', labelFontSize, ...
                    'FontWeight','bold', 'Color', fontColor);
            else
                set(ax, 'YTickLabel', []);
            end

            if r == nRows
                xlabel(ax, 'Hold time (%)', 'FontSize', labelFontSize, 'Color', fontColor);
            else
                set(ax, 'XTickLabel', []);
            end

            xlim(ax, [0 100]);
            xticks(ax, [0 50 100]);
            formatAxis(ax, axisFontSize, fontColor);
        end
    end

    outBase = fullfile(outDir, 'figure7c_repetition_aligned_median_curves');
    exportFigureSet(fig, outBase, exportResolution);
end

fprintf('\nSaved outputs in:\n  %s\n', outDir);

%% ========================================================================
%% LOCAL FUNCTIONS
%% ========================================================================

function D = loadSubjectNormalized(csvFile, baselineSec, nSensors, removeQCSamples)

    if exist(csvFile, 'file') ~= 2
        error('File not found: %s', csvFile);
    end

    try
        opts = detectImportOptions(csvFile, 'VariableNamingRule','preserve');
        T = readtable(csvFile, opts);
    catch
        T = readtable(csvFile);
    end

    vars = T.Properties.VariableNames;

    assert(ismember('elapsed_s', vars), 'Missing elapsed_s in %s', csvFile);
    assert(ismember('position_index', vars), 'Missing position_index in %s', csvFile);

    t = getNumericColumn(T, 'elapsed_s');
    t = t - localNanMin(t);
    pos = round(getNumericColumn(T, 'position_index'));

    if ismember('is_hold', vars)
        isHold = getNumericColumn(T, 'is_hold') == 1;
    else
        isHold = true(size(t));
    end

    n = height(T);
    Y = nan(n, nSensors);

    baseMask = isfinite(t) & t <= baselineSec;
    if nnz(baseMask) < 3
        baseMask = false(size(t));
        baseMask(1:min(n,40)) = true;
    end

    for s = 1:nSensors
        rCol = sprintf('r_s%d_ohm', s);
        drCol = sprintf('dr_s%d', s);

        if ismember(rCol, vars)
            R = getNumericColumn(T, rCol);
            R0 = localNanMedian(R(baseMask));
            if ~isfinite(R0) || abs(R0) < eps
                y = nan(size(R));
            else
                y = (R - R0) ./ R0;
            end
        elseif ismember(drCol, vars)
            y = getNumericColumn(T, drCol);
        else
            error('Missing %s or %s in %s', rCol, drCol, csvFile);
        end

        if removeQCSamples
            hiCol = sprintf('qc_high_adc_s%d', s);
            loCol = sprintf('qc_low_adc_s%d', s);
            if ismember(hiCol, vars) && ismember(loCol, vars)
                bad = getNumericColumn(T, hiCol) ~= 0 | getNumericColumn(T, loCol) ~= 0;
                y(bad) = NaN;
            end
        end

        Y(:,s) = y;
    end

    [t, order] = sort(t);
    D.t = t;
    D.position = pos(order);
    D.is_hold = isHold(order);
    D.dr = Y(order,:);
end

function segments = contiguousSegments(idx)

    segments = {};
    idx = idx(:);

    if isempty(idx)
        return;
    end

    breaks = [1; find(diff(idx) > 1) + 1; numel(idx) + 1];

    for k = 1:(numel(breaks)-1)
        segments{end+1} = idx(breaks(k):(breaks(k+1)-1)); %#ok<AGROW>
    end
end

function x = getNumericColumn(T, colName)

    v = T.(colName);

    if isnumeric(v) || islogical(v)
        x = double(v);
    elseif iscell(v)
        x = str2double(v);
    elseif iscategorical(v)
        x = str2double(cellstr(v));
    else
        x = double(v);
    end

    x = x(:);
end

function [Fvalue, pValue] = anovaOneWayManual(y, group)

    y = y(:);
    group = group(:);

    valid = isfinite(y) & isfinite(group);
    y = y(valid);
    group = group(valid);

    groups = unique(group);
    k = numel(groups);
    N = numel(y);

    dfBetween = k - 1;
    dfWithin = N - k;

    if k < 2 || dfWithin <= 0
        Fvalue = NaN;
        pValue = NaN;
        return;
    end

    grandMean = mean(y);
    ssBetween = 0;
    ssWithin = 0;

    for i = 1:k
        vals = y(group == groups(i));
        ni = numel(vals);
        mi = mean(vals);
        ssBetween = ssBetween + ni*(mi - grandMean)^2;
        ssWithin = ssWithin + sum((vals - mi).^2);
    end

    msBetween = ssBetween / dfBetween;
    msWithin = ssWithin / dfWithin;

    if msWithin == 0
        Fvalue = Inf;
        pValue = 0;
    else
        Fvalue = msBetween / msWithin;
        pValue = 1 - fCdfManual(Fvalue, dfBetween, dfWithin);
    end
end

function p = fCdfManual(x, df1, df2)

    if ~isfinite(x)
        p = double(x > 0);
        return;
    end

    if x <= 0
        p = 0;
        return;
    end

    z = (df1*x) / (df1*x + df2);
    p = betainc(z, df1/2, df2/2);
end

function setDisplayYLimits(ax, y, includeZero, paddingFraction)

    y = y(isfinite(y));
    if isempty(y)
        return;
    end

    lo = min(y);
    hi = max(y);

    if includeZero
        lo = min(lo, 0);
        hi = max(hi, 0);
    end

    if hi <= lo
        pad = max(0.05, 0.10*abs(lo));
    else
        pad = paddingFraction*(hi - lo);
    end

    ylim(ax, [lo-pad hi+pad]);
end

function addZeroReferenceLine(ax, zeroLineColor)

    xl = xlim(ax);
    yl = ylim(ax);

    if yl(1) <= 0 && yl(2) >= 0
        line(ax, xl, [0 0], 'Color', zeroLineColor, ...
            'LineWidth',0.45, 'LineStyle','-', 'HandleVisibility','off');
    end

    xlim(ax, xl);
    ylim(ax, yl);
end

function formatAxis(ax, axisFontSize, fontColor)

    box(ax,'on');
    grid(ax,'on');
    ax.FontSize = axisFontSize;
    ax.LineWidth = 0.50;
    ax.TickDir = 'out';
    ax.Layer = 'top';
    ax.Color = [1 1 1];
    ax.XColor = fontColor;
    ax.YColor = fontColor;

    try
        ax.XMinorGrid = 'off';
        ax.YMinorGrid = 'off';
        ax.GridAlpha = 0.10;
        ax.MinorGridAlpha = 0.00;
    catch
    end

    try
        disableDefaultInteractivity(ax);
        ax.Toolbar.Visible = 'off';
    catch
    end
end

function exportFigureSet(fig, outBase, exportResolution)

    outPng = [outBase '.png'];
    outPdf = [outBase '.pdf'];
    outTif = [outBase '.tif'];

    try
        exportgraphics(fig, outPng, 'Resolution',exportResolution, 'BackgroundColor','white');
    catch
        print(fig, outPng, '-dpng', sprintf('-r%d', exportResolution));
    end

    try
        exportgraphics(fig, outTif, 'Resolution',exportResolution, 'BackgroundColor','white');
    catch
        print(fig, outTif, '-dtiff', sprintf('-r%d', exportResolution));
    end

    try
        exportgraphics(fig, outPdf, 'ContentType','vector', 'BackgroundColor','white');
    catch
        print(fig, outPdf, '-dpdf', '-bestfit');
    end

    fprintf('Saved:\n  %s\n  %s\n  %s\n', outPng, outPdf, outTif);
end

function txt = formatPValue(p)

    if ~isfinite(p)
        txt = 'p = n/a';
    elseif p < 0.001
        txt = 'p < 0.001';
    elseif p < 0.01
        txt = sprintf('p = %.4f', p);
    else
        txt = sprintf('p = %.3f', p);
    end
end

function m = localNanMedian(x)

    x = x(isfinite(x));
    if isempty(x)
        m = NaN;
    else
        m = median(x);
    end
end

function m = localNanMin(x)

    x = x(isfinite(x));
    if isempty(x)
        m = 0;
    else
        m = min(x);
    end
end

function qv = localPercentile(x, q)

    x = sort(x(isfinite(x)));
    n = numel(x);

    if n == 0
        qv = NaN;
        return;
    elseif n == 1
        qv = x(1);
        return;
    end

    q = max(0, min(100, q));
    pos = 1 + (q/100)*(n - 1);
    lo = floor(pos);
    hi = ceil(pos);

    if lo == hi
        qv = x(lo);
    else
        qv = x(lo) + (pos - lo)*(x(hi) - x(lo));
    end
end
