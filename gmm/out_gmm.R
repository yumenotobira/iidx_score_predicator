library(mvtnorm)
library(mclust)

args <- commandArgs(trailingOnly=T)
file <- args[1]
name <- args[2]
difficulty <- args[3]
x <- read.table(file, sep="\t")

file_name <- paste(name, difficulty, sep = "_")

gmmdens <- densityMclust(x[[1]], G = 5, modelNames = "V")

params <- gmmdens$parameters

write(c(params$pro, params$mean, params$variance$sigmasq),
      file = paste("gmm_result/", file_name, sep = ""), append=F, sep = ",")
