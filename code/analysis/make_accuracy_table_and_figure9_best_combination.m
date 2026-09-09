%% make_accuracy_table_and_figure9_best_combination.m
% Exhaustive sensor-combination screening + Figure 9 for the best combination.
%
% This script does two things:
%   1) Evaluates every 1-, 2-, and 3-sensor combination and saves accuracy tables.
%   2) Selects the best 3-sensor combination and generates a Figure-9-style plot:
%      time-series error overlay + confusion matrix.
%
% Inputs expected in data/processed:
%   subject_01.csv, subject_02.csv, subject_03.csv
%
% Subject names are anonymized in all outputs:
%   Subject 1, Subject 2, Subject 3
%
% Recommended workflow:
%   - First run with nRepeats = 1 and nTrees = 60 to check runtime.
%   - For final manuscript results, use nRepeats = 5 or 10 and nTrees = 100-200.
%
% Outputs are saved in:
%   analysis_outputs/
%
% Main outputs:
%   combination_accuracy_detailed.csv
%   combination_accuracy_summary.csv
%   combination_top20.csv
%   best_by_sensor_count_and_holdout.csv
%   figure9_best_combination.png/.pdf/.tif
%   figure9_best_combination_confusion_matrix.csv
%   figure9_best_combination_predictions.csv
%   figure9_best_combination_summary.csv

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

% Evaluate all 1-, 2-, and 3-sensor combinations.
combinationSizes = [1 2 3];

% Test fractions: 0.20 means 20% testing and 80% training.
testFractions = [0.20 0.30 0.50];
testFractionLabels = {'20-80','30-70','50-50'};

% For a quick test, use nRepeats = 1.
% For final manuscript numbers, use nRepeats = 5 or 10.
nRepeats = 1;
randomSeed = 42;

% Figure 9 will use the best combination with this number of sensors.
finalFigureNumSensors = 3;
rankMetric = 'MeanBalancedAccuracy';   % 'MeanBalancedAccuracy' or 'MeanAccuracy'

% Figure 9 representative subject and split.
subjectIndexForFigure9 = 1;
testFractionForFigure9 = 0.50;
repeatIndexForFigure9 = 1;

% Classification settings.
classifierType = 'randomforest';       % 'randomforest', 'knn', or 'nearestcentroid'
nTrees = 80;
minLeafSize = 2;
useUniformClassPrior = true;           % helps reduce majority-class bias

% Important: use full protocol for Figure 9 so transition errors are visible.
% Set true only if you want steady-state posture recognition.
useHoldOnlyForClassification = false;

% Feature settings.
% Current-only features reproduce a simple instantaneous classifier.
% Temporal features usually improve performance for textile signals.
useTemporalFeatures = true;
shortWindowSamples = 5;                % about 0.25 s if sampling is 20 Hz
longWindowSamples = 20;                % about 1 s if sampling is 20 Hz

% Confusion-matrix display.
% 'rowpercent' is easier to interpret with class imbalance.
% 'counts' matches the reference-style raw count matrix.
confusionDisplayMode = 'rowpercent';   % 'rowpercent' or 'counts'

% Figure/export settings.
outDir = fullfile(repoRoot, 'results', 'analysis');
outBaseNameFig9 = 'figure9_best_combination';
exportResolution = 600;
figWidthCm = 28;
figHeightCm = 15.5;
maxErrorMarkersPerTrace = 350;

% Pastel posture background colors.
showPostureBackground = true;
postureAlpha = 1.00;
postureColors = [ ...
    1.00 0.89 0.82;  ... % peach
    0.76 0.90 0.95;  ... % pale cyan
    0.84 0.94 0.79;  ... % pale green
    0.85 0.91 0.96;  ... % pale blue-grey
    1.00 0.98 0.78;  ... % pale yellow
    0.83 0.93 0.78;  ... % soft green
    0.82 0.80 0.96;  ... % lavender
    0.95 0.86 0.96];     % pale violet/pink
restPositionForBlocks = 1;
backgroundColorMode = 'blockOrder';

if exist(outDir, 'dir') ~= 7
    mkdir(outDir);
end

%% ---------------- LOAD AND PRECOMPUTE FEATURES ----------------
fprintf('Loading data and computing features...\n');
D = cell(numel(files),1);

for subjIdx = 1:numel(files)
    D{subjIdx} = loadSubjectForClassification( ...
        fullfile(dataDir, files{subjIdx}), baselineSec, nSensors, ...
        useTemporalFeatures, shortWindowSamples, longWindowSamples);
    D{subjIdx}.subjectLabel = subjectLabels{subjIdx};
    fprintf('  %s: %d samples, %d features\n', subjectLabels{subjIdx}, ...
        numel(D{subjIdx}.y), size(D{subjIdx}.Xfeatures,2));
end

featuresPerSensor = D{1}.featuresPerSensor;
featureNamesPerSensor = D{1}.featureNamesPerSensor;

%% ---------------- GENERATE SENSOR COMBINATIONS ----------------
combos = {};
comboSizes = [];
for k = combinationSizes
    C = nchoosek(1:nSensors, k);
    for i = 1:size(C,1)
        combos{end+1,1} = C(i,:); %#ok<SAGROW>
        comboSizes(end+1,1) = k; %#ok<SAGROW>
    end
end

fprintf('Evaluating %d sensor combinations across %d subjects, %d holdouts, %d repeat(s).\n', ...
    numel(combos), numel(files), numel(testFractions), nRepeats);

%% ---------------- EXHAUSTIVE COMBINATION EVALUATION ----------------
detailRows = struct([]);
rowCounter = 0;
tic;

for comboIdx = 1:numel(combos)

    sensors = combos{comboIdx};
    comboStr = sensorsToString(sensors);

    for hIdx = 1:numel(testFractions)

        testFraction = testFractions(hIdx);
        holdoutLabel = testFractionLabels{hIdx};

        for rep = 1:nRepeats

            for subjIdx = 1:numel(D)

                seed = randomSeed + 100000*comboIdx + 1000*hIdx + 100*rep + subjIdx;

                [acc, bacc, cm] = evaluateOneCombination( ...
                    D{subjIdx}, sensors, featuresPerSensor, positions, ...
                    testFraction, seed, classifierType, nTrees, minLeafSize, ...
                    useUniformClassPrior, useHoldOnlyForClassification);

                rowCounter = rowCounter + 1;
                detailRows(rowCounter).Combination = comboStr; %#ok<SAGROW>
                detailRows(rowCounter).NumSensors = numel(sensors); %#ok<SAGROW>
                detailRows(rowCounter).SensorNumbers = mat2str(sensors); %#ok<SAGROW>
                detailRows(rowCounter).Holdout = holdoutLabel; %#ok<SAGROW>
                detailRows(rowCounter).TestFraction = testFraction; %#ok<SAGROW>
                detailRows(rowCounter).Repeat = rep; %#ok<SAGROW>
                detailRows(rowCounter).SubjectIndex = subjIdx; %#ok<SAGROW>
                detailRows(rowCounter).Subject = string(D{subjIdx}.subjectLabel); %#ok<SAGROW>
                detailRows(rowCounter).Accuracy = acc; %#ok<SAGROW>
                detailRows(rowCounter).BalancedAccuracy = bacc; %#ok<SAGROW>
                detailRows(rowCounter).Correct = sum(diag(cm)); %#ok<SAGROW>
                detailRows(rowCounter).Total = sum(cm(:)); %#ok<SAGROW>
            end
        end
    end

    if mod(comboIdx,25) == 0 || comboIdx == numel(combos)
        fprintf('  Completed %d/%d combinations in %.1f s. Last: %s\n', ...
            comboIdx, numel(combos), toc, comboStr);
    end
end

detailTable = struct2table(detailRows);

outDetailed = fullfile(outDir, 'combination_accuracy_detailed.csv');
writetable(detailTable, outDetailed);

%% ---------------- SUMMARIZE COMBINATIONS ----------------
summaryTable = summarizeCombinationResults(detailTable, testFractionLabels);

% Sort by ranking metric.
if strcmpi(rankMetric, 'MeanAccuracy')
    summaryTable = sortrows(summaryTable, 'MeanAccuracy', 'descend');
else
    summaryTable = sortrows(summaryTable, 'MeanBalancedAccuracy', 'descend');
end

outSummary = fullfile(outDir, 'combination_accuracy_summary.csv');
writetable(summaryTable, outSummary);

nTop = min(20, height(summaryTable));
top20Table = summaryTable(1:nTop,:);
outTop20 = fullfile(outDir, 'combination_top20.csv');
writetable(top20Table, outTop20);

bestBySizeHoldoutTable = summarizeBestBySizeAndHoldout(detailTable, combinationSizes, testFractionLabels);
outBestBySizeHoldout = fullfile(outDir, 'best_by_sensor_count_and_holdout.csv');
writetable(bestBySizeHoldoutTable, outBestBySizeHoldout);

fprintf('\nTop combinations by %s:\n', rankMetric);
disp(top20Table(:, {'Combination','NumSensors','MeanAccuracy','MeanBalancedAccuracy'}));

%% ---------------- SELECT BEST COMBINATION FOR FIGURE 9 ----------------
bestCandidates = summaryTable(summaryTable.NumSensors == finalFigureNumSensors, :);
if isempty(bestCandidates)
    error('No combinations found with %d sensors.', finalFigureNumSensors);
end

bestRow = bestCandidates(1,:);
bestSensors = parseSensorString(bestRow.SensorNumbers{1});
bestComboStr = bestRow.Combination{1};

fprintf('\nSelected best %d-sensor combination for Figure 9: %s\n', ...
    finalFigureNumSensors, bestComboStr);
fprintf('  Mean accuracy = %.4f\n', bestRow.MeanAccuracy);
fprintf('  Mean balanced accuracy = %.4f\n', bestRow.MeanBalancedAccuracy);

%% ---------------- TRAIN FIGURE 9 MODEL ON REPRESENTATIVE SUBJECT ----------------
subjData = D{subjectIndexForFigure9};
seedFig = randomSeed + 999000 + repeatIndexForFigure9;

[figResult] = trainPredictForFigure( ...
    subjData, bestSensors, featuresPerSensor, positions, testFractionForFigure9, ...
    seedFig, classifierType, nTrees, minLeafSize, useUniformClassPrior, ...
    useHoldOnlyForClassification);

outCM = fullfile(outDir, 'figure9_best_combination_confusion_matrix.csv');
cmTable = array2table(figResult.cmCounts, ...
    'VariableNames', strcat('Predicted_', string(positions)), ...
    'RowNames', strcat('True_', string(positions)));
writetable(cmTable, outCM, 'WriteRowNames', true);

outPred = fullfile(outDir, 'figure9_best_combination_predictions.csv');
predTable = table( ...
    subjData.t(figResult.testOriginalIndex), ...
    figResult.testOriginalIndex(:), ...
    figResult.yTrue(:), ...
    figResult.yPred(:), ...
    figResult.correct(:), ...
    'VariableNames', {'Time_s','SampleIndex','TruePosition','PredictedPosition','Correct'});
writetable(predTable, outPred);

figSummary = table( ...
    string(bestComboStr), mat2str(bestSensors), subjectIndexForFigure9, ...
    string(subjData.subjectLabel), testFractionForFigure9, figResult.accuracy, ...
    figResult.balancedAccuracy, string(classifierType), useTemporalFeatures, ...
    'VariableNames', {'Combination','SensorNumbers','SubjectIndex','Subject', ...
    'TestFraction','Accuracy','BalancedAccuracy','Classifier','TemporalFeatures'});
writetable(figSummary, fullfile(outDir, 'figure9_best_combination_summary.csv'));

%% ---------------- MAKE FIGURE 9 ----------------
fig = makeFigure9( ...
    subjData, bestSensors, figResult, positions, bestComboStr, ...
    confusionDisplayMode, figWidthCm, figHeightCm, maxErrorMarkersPerTrace, ...
    showPostureBackground, postureColors, postureAlpha, restPositionForBlocks, backgroundColorMode);

outPng = fullfile(outDir, [outBaseNameFig9 '.png']);
outPdf = fullfile(outDir, [outBaseNameFig9 '.pdf']);
outTif = fullfile(outDir, [outBaseNameFig9 '.tif']);

try
    exportgraphics(fig, outPng, 'Resolution', exportResolution, 'BackgroundColor','white');
catch
    print(fig, outPng, '-dpng', sprintf('-r%d', exportResolution));
end

try
    exportgraphics(fig, outTif, 'Resolution', exportResolution, 'BackgroundColor','white');
catch
    print(fig, outTif, '-dtiff', sprintf('-r%d', exportResolution));
end

try
    exportgraphics(fig, outPdf, 'ContentType','vector', 'BackgroundColor','white');
catch
    print(fig, outPdf, '-dpdf', '-bestfit');
end

fprintf('\nSaved outputs:\n');
fprintf('  %s\n', outDetailed);
fprintf('  %s\n', outSummary);
fprintf('  %s\n', outTop20);
fprintf('  %s\n', outBestBySizeHoldout);
fprintf('  %s\n', outPng);
fprintf('  %s\n', outPdf);
fprintf('  %s\n', outTif);
fprintf('  %s\n', outCM);
fprintf('  %s\n', outPred);

%% ========================================================================
%% LOCAL FUNCTIONS
%% ========================================================================

function D = loadSubjectForClassification(csvFile, baselineSec, nSensors, useTemporalFeatures, shortW, longW)

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

    y = round(getNumericColumn(T, 'position_index'));

    if ismember('is_hold', vars)
        isHold = getNumericColumn(T, 'is_hold') == 1;
    else
        isHold = true(size(y));
    end

    n = height(T);
    dr = nan(n, nSensors);
    R0 = nan(1, nSensors);

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
            R0(s) = localNanMedian(R(baseMask));
            if isfinite(R0(s)) && abs(R0(s)) > eps
                dr(:,s) = (R - R0(s)) ./ R0(s);
            end
        elseif ismember(drCol, vars)
            dr(:,s) = getNumericColumn(T, drCol);
        else
            error('Missing %s or %s in %s', rCol, drCol, csvFile);
        end

        hiCol = sprintf('qc_high_adc_s%d', s);
        loCol = sprintf('qc_low_adc_s%d', s);
        if ismember(hiCol, vars) && ismember(loCol, vars)
            bad = getNumericColumn(T, hiCol) ~= 0 | getNumericColumn(T, loCol) ~= 0;
            dr(bad,s) = NaN;
        end
    end

    valid = isfinite(t) & isfinite(y) & y >= 1 & y <= 8;

    [Xfeatures, featureNamesPerSensor] = makeFeatureMatrix(dr, useTemporalFeatures, shortW, longW);

    D.t = t(valid);
    D.y = y(valid);
    D.isHold = isHold(valid);
    D.dr = dr(valid,:);
    D.Xfeatures = Xfeatures(valid,:);
    D.R0 = R0;
    D.featuresPerSensor = numel(featureNamesPerSensor);
    D.featureNamesPerSensor = featureNamesPerSensor;
end

function [X, featureNames] = makeFeatureMatrix(dr, useTemporalFeatures, shortW, longW)

    [n, nSensors] = size(dr);

    if useTemporalFeatures
        featureNames = { ...
            'value', ...
            'slope', ...
            sprintf('mean_%d', shortW), ...
            sprintf('std_%d', shortW), ...
            sprintf('mean_%d', longW), ...
            sprintf('std_%d', longW)};
    else
        featureNames = {'value'};
    end

    f = numel(featureNames);
    X = nan(n, nSensors*f);

    for s = 1:nSensors

        y = dr(:,s);
        col0 = (s-1)*f;

        if useTemporalFeatures
            slope = [0; diff(y)];
            mShort = movmean(y, [shortW-1 0], 'omitnan');
            sdShort = movstd(y, [shortW-1 0], 'omitnan');
            mLong = movmean(y, [longW-1 0], 'omitnan');
            sdLong = movstd(y, [longW-1 0], 'omitnan');

            sdShort(~isfinite(sdShort)) = 0;
            sdLong(~isfinite(sdLong)) = 0;
            slope(~isfinite(slope)) = 0;

            X(:,col0+1) = y;
            X(:,col0+2) = slope;
            X(:,col0+3) = mShort;
            X(:,col0+4) = sdShort;
            X(:,col0+5) = mLong;
            X(:,col0+6) = sdLong;
        else
            X(:,col0+1) = y;
        end
    end
end

function [acc, bacc, cm] = evaluateOneCombination(D, sensors, featuresPerSensor, positions, testFraction, seed, classifierType, nTrees, minLeafSize, useUniformPrior, useHoldOnly)

    result = trainPredictForFigure(D, sensors, featuresPerSensor, positions, testFraction, seed, classifierType, nTrees, minLeafSize, useUniformPrior, useHoldOnly);
    acc = result.accuracy;
    bacc = result.balancedAccuracy;
    cm = result.cmCounts;
end

function result = trainPredictForFigure(D, sensors, featuresPerSensor, positions, testFraction, seed, classifierType, nTrees, minLeafSize, useUniformPrior, useHoldOnly)

    featureCols = sensorFeatureColumns(sensors, featuresPerSensor);

    X = D.Xfeatures(:, featureCols);
    y = D.y(:);

    if useHoldOnly
        baseMask = D.isHold(:) == 1;
    else
        baseMask = true(size(y));
    end

    baseMask = baseMask & isfinite(y) & y >= min(positions) & y <= max(positions);

    originalIndex = find(baseMask);
    X = X(baseMask,:);
    y = y(baseMask);

    [trainLocal, testLocal] = stratifiedHoldout(y, positions, testFraction, seed);

    XTrainRaw = X(trainLocal,:);
    yTrain = y(trainLocal);
    XTestRaw = X(testLocal,:);
    yTest = y(testLocal);

    [XTrain, XTest] = preprocessTrainTest(XTrainRaw, XTestRaw);

    yPred = trainAndPredictClassifier(XTrain, yTrain, XTest, classifierType, nTrees, minLeafSize, positions, useUniformPrior);
    yPred = round(double(yPred(:)));

    cm = confusionmatFixed(yTest, yPred, positions);
    acc = sum(diag(cm)) / max(1, sum(cm(:)));
    bacc = balancedAccuracyFromCM(cm);

    result.yTrue = yTest(:);
    result.yPred = yPred(:);
    result.correct = yPred(:) == yTest(:);
    result.cmCounts = cm;
    result.accuracy = acc;
    result.balancedAccuracy = bacc;
    result.trainOriginalIndex = originalIndex(trainLocal);
    result.testOriginalIndex = originalIndex(testLocal);
    result.sensors = sensors;
end

function featureCols = sensorFeatureColumns(sensors, featuresPerSensor)

    featureCols = [];
    for s = sensors(:)'
        featureCols = [featureCols, ((s-1)*featuresPerSensor + 1):(s*featuresPerSensor)]; %#ok<AGROW>
    end
end

function [trainIdx, testIdx] = stratifiedHoldout(y, positions, testFraction, seed)

    rng(seed, 'twister');

    y = y(:);
    trainIdx = false(size(y));
    testIdx = false(size(y));

    for p = positions
        idx = find(y == p);
        idx = idx(randperm(numel(idx)));
        nTest = max(1, round(testFraction * numel(idx)));
        nTest = min(nTest, numel(idx)-1);
        testIdx(idx(1:nTest)) = true;
        trainIdx(idx(nTest+1:end)) = true;
    end
end

function [XTrain, XTest] = preprocessTrainTest(XTrainRaw, XTestRaw)

    % Median imputation using training split only.
    med = nanmedianLocal(XTrainRaw, 1);
    med(~isfinite(med)) = 0;

    XTrain = XTrainRaw;
    XTest = XTestRaw;

    for j = 1:size(XTrain,2)
        badTrain = ~isfinite(XTrain(:,j));
        badTest = ~isfinite(XTest(:,j));
        XTrain(badTrain,j) = med(j);
        XTest(badTest,j) = med(j);
    end

    % Z-score using training split only.
    mu = mean(XTrain, 1);
    sigma = std(XTrain, 0, 1);
    sigma(~isfinite(sigma) | sigma < eps) = 1;

    XTrain = (XTrain - mu) ./ sigma;
    XTest = (XTest - mu) ./ sigma;
end

function yPred = trainAndPredictClassifier(XTrain, yTrain, XTest, classifierType, nTrees, minLeafSize, positions, useUniformPrior)

    classifierType = lower(classifierType);

    switch classifierType

        case 'randomforest'

            if exist('fitcensemble', 'file') == 2
                t = templateTree('MinLeafSize', minLeafSize);

                args = {'Method','Bag', ...
                        'NumLearningCycles', nTrees, ...
                        'Learners', t, ...
                        'ClassNames', positions};

                if useUniformPrior
                    args = [args, {'Prior','uniform'}]; %#ok<AGROW>
                end

                mdl = fitcensemble(XTrain, yTrain, args{:});
                yPred = predict(mdl, XTest);

            elseif exist('TreeBagger', 'file') == 2

                classNames = cellstr(string(positions));
                yTrainCat = categorical(yTrain, positions, classNames);

                mdl = TreeBagger(nTrees, XTrain, yTrainCat, ...
                    'Method','classification', ...
                    'MinLeafSize', minLeafSize, ...
                    'OOBPrediction','off', ...
                    'ClassNames', classNames);

                yPredCell = predict(mdl, XTest);
                yPred = str2double(yPredCell);

            else
                warning('Random Forest unavailable. Falling back to nearest centroid classifier.');
                yPred = nearestCentroidPredict(XTrain, yTrain, XTest, positions);
            end

        case 'knn'

            if exist('fitcknn', 'file') == 2
                mdl = fitcknn(XTrain, yTrain, ...
                    'NumNeighbors', 5, ...
                    'Standardize', false, ...
                    'ClassNames', positions);
                yPred = predict(mdl, XTest);
            else
                warning('fitcknn unavailable. Falling back to nearest centroid classifier.');
                yPred = nearestCentroidPredict(XTrain, yTrain, XTest, positions);
            end

        otherwise
            yPred = nearestCentroidPredict(XTrain, yTrain, XTest, positions);
    end
end

function yPred = nearestCentroidPredict(XTrain, yTrain, XTest, positions)

    centroids = nan(numel(positions), size(XTrain,2));
    for i = 1:numel(positions)
        p = positions(i);
        centroids(i,:) = localNanMeanRows(XTrain(yTrain == p, :));
    end

    yPred = nan(size(XTest,1),1);
    for i = 1:size(XTest,1)
        d = sum((centroids - XTest(i,:)).^2, 2);
        [~,m] = min(d);
        yPred(i) = positions(m);
    end
end

function cm = confusionmatFixed(yTrue, yPred, positions)

    cm = zeros(numel(positions), numel(positions));
    for i = 1:numel(yTrue)
        r = find(positions == yTrue(i), 1);
        c = find(positions == yPred(i), 1);
        if ~isempty(r) && ~isempty(c)
            cm(r,c) = cm(r,c) + 1;
        end
    end
end

function bacc = balancedAccuracyFromCM(cm)

    denom = sum(cm,2);
    recall = diag(cm) ./ denom;
    recall(~isfinite(recall)) = NaN;
    bacc = localNanMean(recall);
end

function summaryTable = summarizeCombinationResults(detailTable, holdoutLabels)

    combos = unique(detailTable.Combination, 'stable');
    rows = struct([]);

    for i = 1:numel(combos)
        combo = combos{i};
        mask = strcmp(detailTable.Combination, combo);
        T = detailTable(mask,:);

        rows(i).Combination = combo; %#ok<SAGROW>
        rows(i).NumSensors = T.NumSensors(1); %#ok<SAGROW>
        rows(i).SensorNumbers = T.SensorNumbers{1}; %#ok<SAGROW>
        rows(i).MeanAccuracy = localNanMean(T.Accuracy); %#ok<SAGROW>
        rows(i).SDAccuracy = localNanStd(T.Accuracy); %#ok<SAGROW>
        rows(i).MeanBalancedAccuracy = localNanMean(T.BalancedAccuracy); %#ok<SAGROW>
        rows(i).SDBalancedAccuracy = localNanStd(T.BalancedAccuracy); %#ok<SAGROW>
        rows(i).N_Evaluations = height(T); %#ok<SAGROW>

        for h = 1:numel(holdoutLabels)
            label = holdoutLabels{h};
            fieldLabel = strrep(label, '-', '_');
            mh = strcmp(T.Holdout, label);
            rows(i).(['Accuracy_' fieldLabel]) = localNanMean(T.Accuracy(mh)); %#ok<SAGROW>
            rows(i).(['BalancedAccuracy_' fieldLabel]) = localNanMean(T.BalancedAccuracy(mh)); %#ok<SAGROW>
        end
    end

    summaryTable = struct2table(rows);
end

function bestTable = summarizeBestBySizeAndHoldout(detailTable, combinationSizes, holdoutLabels)

    rows = struct([]);
    r = 0;

    for k = combinationSizes
        for h = 1:numel(holdoutLabels)
            label = holdoutLabels{h};
            mask = detailTable.NumSensors == k & strcmp(detailTable.Holdout, label);
            T = detailTable(mask,:);
            combos = unique(T.Combination, 'stable');

            bestCombo = '';
            bestSensors = '';
            bestAcc = NaN;
            bestBAcc = -Inf;

            for i = 1:numel(combos)
                c = combos{i};
                m = strcmp(T.Combination, c);
                meanB = localNanMean(T.BalancedAccuracy(m));
                meanA = localNanMean(T.Accuracy(m));
                if meanB > bestBAcc
                    bestBAcc = meanB;
                    bestAcc = meanA;
                    bestCombo = c;
                    bestSensors = T.SensorNumbers{find(m,1,'first')};
                end
            end

            r = r + 1;
            rows(r).NumSensors = k; %#ok<SAGROW>
            rows(r).Holdout = label; %#ok<SAGROW>
            rows(r).BestCombination = bestCombo; %#ok<SAGROW>
            rows(r).SensorNumbers = bestSensors; %#ok<SAGROW>
            rows(r).MeanAccuracy = bestAcc; %#ok<SAGROW>
            rows(r).MeanBalancedAccuracy = bestBAcc; %#ok<SAGROW>
        end
    end

    bestTable = struct2table(rows);
end

function fig = makeFigure9(D, bestSensors, figResult, positions, bestComboStr, confusionMode, figWidthCm, figHeightCm, maxErrorMarkers, showBg, postureColors, postureAlpha, restPosition, colorMode)

    fontColor = [0 0 0];
    traceColor = [0 0 0];
    errorColor = [0.85 0.10 0.10];

    fig = figure('Color','w', 'Units','centimeters', 'Position',[2 2 figWidthCm figHeightCm]);
    try
        set(fig, 'Renderer', 'opengl');
        set(fig, 'InvertHardcopy', 'off');
    catch
    end

    tl = tiledlayout(fig, 3, 2, 'Padding','compact', 'TileSpacing','compact');
    title(tl, sprintf('Best three-sensor classification performance (%s)', D.subjectLabel), ...
        'FontWeight','bold', 'FontSize',14, 'Color',fontColor);

    % Left panel: time-series overlay for selected raw normalized sensors.
    for i = 1:numel(bestSensors)
        s = bestSensors(i);
        ax = nexttile(tl, (i-1)*2 + 1);
        hold(ax,'on');

        y = D.dr(:,s);
        t = D.t;
        xlim(ax, [min(t) max(t)]);
        setRobustYLimits(ax, y, [0.5 99.5], true);

        if showBg
            addPostureBlockBackground(ax, D.t, D.y, postureColors, postureAlpha, restPosition, colorMode);
        end

        addZeroReferenceLine(ax, [0.45 0.45 0.45]);
        hTrace = plot(ax, t, y, '-', 'Color', traceColor, 'LineWidth', 0.65);

        misOrig = figResult.testOriginalIndex(~figResult.correct);
        misOrig = misOrig(isfinite(y(misOrig)));
        if numel(misOrig) > maxErrorMarkers
            pick = unique(round(linspace(1, numel(misOrig), maxErrorMarkers)));
            misPlot = misOrig(pick);
        else
            misPlot = misOrig;
        end

        hErr = plot(ax, t(misPlot), y(misPlot), 'o', ...
            'MarkerSize', 3.5, 'MarkerFaceColor', errorColor, ...
            'MarkerEdgeColor', errorColor, 'LineWidth', 0.4);

        ylabel(ax, {sprintf('S%d', s), '\DeltaR/R_0'}, ...
            'Interpreter','tex', 'FontWeight','bold', 'Color',fontColor);

        if i == 1
            title(ax, sprintf('a) Time-series error overlay: %s', bestComboStr), ...
                'FontWeight','normal', 'Color',fontColor);
            legend(ax, [hTrace hErr], {'Sensor signal','Misclassified test sample'}, ...
                'Location','northeast', 'Box','off', 'TextColor',fontColor, 'FontSize',7);
        end

        if i < numel(bestSensors)
            set(ax, 'XTickLabel', []);
        else
            xlabel(ax, 'Time (s)', 'FontWeight','bold', 'Color',fontColor);
        end

        formatAxisBlack(ax, fontColor);
        try
            uistack(hTrace, 'top');
            uistack(hErr, 'top');
        catch
        end
    end

    % Right panel: confusion matrix.
    axCM = nexttile(tl, [3 1]);
    hold(axCM,'on');

    cmCounts = figResult.cmCounts;

    switch lower(confusionMode)
        case 'rowpercent'
            rowSums = sum(cmCounts,2);
            C = 100 * cmCounts ./ rowSums;
            C(~isfinite(C)) = 0;
            cbLabel = 'Row-normalized count (%)';
            fmt = '%.0f';
            climVals = [0 100];
        otherwise
            C = cmCounts;
            cbLabel = 'Count';
            fmt = '%.0f';
            climVals = [0 max(C(:))];
    end

    imagesc(axCM, positions, positions, C);
    axis(axCM, 'image');
    set(axCM, 'YDir','normal');
    colormap(axCM, pastelBlueMap(256, 0.28));
    if climVals(2) > climVals(1)
        caxis(axCM, climVals);
    end

    cb = colorbar(axCM);
    cb.Label.String = cbLabel;
    cb.Label.Color = fontColor;
    cb.Color = fontColor;

    xlabel(axCM, 'Predicted position', 'FontWeight','bold', 'Color',fontColor);
    ylabel(axCM, 'True position', 'FontWeight','bold', 'Color',fontColor);
    title(axCM, sprintf('b) Confusion matrix\nAccuracy = %.1f%%, balanced accuracy = %.1f%%', ...
        100*figResult.accuracy, 100*figResult.balancedAccuracy), ...
        'FontWeight','normal', 'Color',fontColor);

    xticks(axCM, positions);
    yticks(axCM, positions);

    % Draw white grid lines.
    for k = 0.5:1:8.5
        line(axCM, [0.5 8.5], [k k], 'Color','w', 'LineWidth',0.5, 'HandleVisibility','off');
        line(axCM, [k k], [0.5 8.5], 'Color','w', 'LineWidth',0.5, 'HandleVisibility','off');
    end

    % Cell text.
    maxVal = max(C(:));
    if maxVal <= 0
        maxVal = 1;
    end
    for r = 1:numel(positions)
        for c = 1:numel(positions)
            val = C(r,c);
            if val >= 0.55*maxVal
                txtColor = [1 1 1];
            else
                txtColor = [0 0 0];
            end
            if strcmpi(confusionMode, 'rowpercent')
                label = sprintf([fmt '%%'], val);
            else
                label = sprintf(fmt, val);
            end
            text(axCM, positions(c), positions(r), label, ...
                'HorizontalAlignment','center', 'VerticalAlignment','middle', ...
                'FontSize',7.2, 'FontWeight','bold', 'Color',txtColor);
        end
    end

    formatAxisBlack(axCM, fontColor);

    try
        disableDefaultInteractivity(axCM);
        axCM.Toolbar.Visible = 'off';
    catch
    end
end

function cmap = pastelBlueMap(n, pastelBlend)

    if nargin < 1
        n = 256;
    end
    if nargin < 2
        pastelBlend = 0.30;
    end

    base = [ ...
        0.94 0.97 1.00; ...
        0.80 0.89 0.97; ...
        0.60 0.77 0.91; ...
        0.36 0.61 0.82; ...
        0.13 0.35 0.65; ...
        0.03 0.18 0.40];

    x = linspace(0,1,size(base,1));
    xi = linspace(0,1,n);
    cmap = interp1(x, base, xi, 'linear');
    cmap = (1-pastelBlend)*cmap + pastelBlend*ones(size(cmap));
    cmap(cmap > 1) = 1;
end

function addPostureBlockBackground(ax, t, pos, postureColors, postureAlpha, restPosition, colorMode)

    if nargin < 6
        restPosition = 1;
    end
    if nargin < 7 || isempty(colorMode)
        colorMode = 'blockOrder';
    end

    t = t(:);
    pos = round(pos(:));

    valid = isfinite(t) & isfinite(pos);
    t = t(valid);
    pos = pos(valid);

    if numel(t) < 2
        return;
    end

    [t, order] = sort(t);
    pos = pos(order);

    xl = xlim(ax);
    yl = ylim(ax);
    hold(ax,'on');

    nColors = size(postureColors, 1);
    blocks = [];

    if ~isempty(restPosition) && isfinite(restPosition)
        activeMask = pos ~= restPosition;
        if nnz(activeMask) >= 2
            ta = t(activeMask);
            pa = pos(activeMask);
            runStart = [1; find(diff(pa) ~= 0) + 1];
            runEnd = [runStart(2:end) - 1; numel(pa)];
            targetPosture = pa(runStart);
            targetStart = ta(runStart);
            targetEnd = ta(runEnd);
            nBlocks = numel(targetPosture);
            if nBlocks >= 1
                leftEdge = zeros(nBlocks,1);
                rightEdge = zeros(nBlocks,1);
                leftEdge(1) = xl(1);
                for b = 2:nBlocks
                    boundary = 0.5*(targetEnd(b-1) + targetStart(b));
                    boundary = max(xl(1), min(xl(2), boundary));
                    rightEdge(b-1) = boundary;
                    leftEdge(b) = boundary;
                end
                rightEdge(end) = xl(2);
                blocks = [leftEdge, rightEdge, targetPosture(:), (1:nBlocks)'];
            end
        end
    end

    if isempty(blocks)
        changeIdx = [1; find(diff(pos) ~= 0) + 1; numel(pos) + 1];
        nBlocks = numel(changeIdx) - 1;
        blocks = nan(nBlocks, 4);
        for b = 1:nBlocks
            i1 = changeIdx(b);
            i2 = changeIdx(b+1) - 1;
            blocks(b,:) = [t(i1), t(i2), pos(i1), b];
        end
    end

    patchHandles = gobjects(0);
    for b = 1:size(blocks,1)
        x1 = max(xl(1), blocks(b,1));
        x2 = min(xl(2), blocks(b,2));
        if ~isfinite(x1) || ~isfinite(x2) || x2 <= x1
            continue;
        end
        if strcmpi(colorMode, 'positionIndex')
            colorID = blocks(b,3);
        else
            colorID = blocks(b,4);
        end
        colorID = round(colorID);
        if ~isfinite(colorID)
            continue;
        end
        colorID = 1 + mod(colorID - 1, nColors);
        p = patch(ax, [x1 x2 x2 x1], [yl(1) yl(1) yl(2) yl(2)], ...
            postureColors(colorID,:), 'EdgeColor','none', ...
            'FaceAlpha', postureAlpha, 'HandleVisibility','off');
        patchHandles(end+1) = p; %#ok<AGROW>
    end

    xlim(ax, xl);
    ylim(ax, yl);
    try
        if ~isempty(patchHandles)
            uistack(patchHandles, 'bottom');
        end
    catch
    end
end

function addZeroReferenceLine(ax, color)
    xl = xlim(ax);
    yl = ylim(ax);
    if yl(1) <= 0 && yl(2) >= 0
        line(ax, xl, [0 0], 'Color', color, 'LineWidth',0.35, 'HandleVisibility','off');
    end
    xlim(ax, xl); ylim(ax, yl);
end

function setRobustYLimits(ax, y, pct, includeZero)
    y = y(isfinite(y));
    if isempty(y)
        return;
    end
    lo = localPercentile(y, pct(1));
    hi = localPercentile(y, pct(2));
    if includeZero
        lo = min(lo, 0); hi = max(hi, 0);
    end
    if hi <= lo
        pad = max(0.05, 0.10*abs(lo));
    else
        pad = 0.08*(hi-lo);
    end
    ylim(ax, [lo-pad hi+pad]);
end

function formatAxisBlack(ax, fontColor)
    ax.Color = [1 1 1];
    ax.XColor = fontColor;
    ax.YColor = fontColor;
    ax.LineWidth = 0.6;
    ax.FontSize = 8;
    ax.TickDir = 'out';
    ax.Layer = 'top';
    box(ax,'on');
    grid(ax,'on');
    try
        ax.GridAlpha = 0.13;
        ax.XMinorGrid = 'off';
        ax.YMinorGrid = 'off';
    catch
    end
    try
        ax.Title.Color = fontColor;
        ax.XLabel.Color = fontColor;
        ax.YLabel.Color = fontColor;
    catch
    end
    try
        disableDefaultInteractivity(ax);
        ax.Toolbar.Visible = 'off';
    catch
    end
end

function comboStr = sensorsToString(sensors)
    parts = cell(1,numel(sensors));
    for i = 1:numel(sensors)
        parts{i} = sprintf('S%d', sensors(i));
    end
    comboStr = strjoin(parts, '-');
end

function sensors = parseSensorString(sensorNumbersString)
    % Accepts strings such as '[2 3 8]' or numeric arrays.
    if isnumeric(sensorNumbersString)
        sensors = sensorNumbersString;
        return;
    end
    if isstring(sensorNumbersString)
        sensorNumbersString = char(sensorNumbersString);
    end
    sensors = str2num(sensorNumbersString); %#ok<ST2NM>
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

function rowMean = localNanMeanRows(X)
    if isempty(X)
        rowMean = nan(1, size(X,2));
        return;
    end
    rowMean = nan(1, size(X,2));
    for j = 1:size(X,2)
        rowMean(j) = localNanMean(X(:,j));
    end
end

function m = localNanMean(x)
    x = x(isfinite(x));
    if isempty(x)
        m = NaN;
    else
        m = mean(x);
    end
end

function s = localNanStd(x)
    x = x(isfinite(x));
    if numel(x) < 2
        s = NaN;
    else
        s = std(x);
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

function med = nanmedianLocal(X, dim)
    if nargin < 2
        dim = 1;
    end
    if dim ~= 1
        error('nanmedianLocal currently supports dim = 1 only.');
    end
    med = nan(1,size(X,2));
    for j = 1:size(X,2)
        med(j) = localNanMedian(X(:,j));
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
