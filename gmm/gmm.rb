musics = `ls #{File.expand_path("../result_distribution", __FILE__)}`.split("\n")

musics.each do |music|
  name, difficulty = music.split(/_(ANOTHER|HYPER)/)
  file = File.expand_path("../result_distribution/#{name}_#{difficulty}", __FILE__)
  `R --vanilla --slave --args "#{file}" "#{name}" "#{difficulty}" < #{File.expand_path("../out_gmm.R", __FILE__)}`
end
