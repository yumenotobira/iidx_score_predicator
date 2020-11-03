files = `ls #{File.expand_path("../chart_encoded", __FILE__)}`.split("\n")

files.each do |file|
  chart = []
  File.open(File.expand_path("../chart_encoded/#{file}", __FILE__)) do |f|
    f.each_line do |line|
      t = line.chomp.split(",").map(&:to_i)
      8.times do |i|
        if t[i+8] == 1 && t[i] == 0
          t[i] = 0.5
        end
      end
      t = t[0..7] + [t[16]]
      chart << t
    end
  end

  File.open(File.expand_path("../8keys_encoded/#{file}", __FILE__), "w") do |f|
    chart.each do |t|
      f.puts t.join(",")
    end
  end
end
