const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const title = process.argv[2];

if (!title) {
  console.error('Usage: npm run new "Article Title"');
  process.exit(1);
}

try {
  // Execute qiita new
  console.log(`Creating new article: "${title}"...`);
  const stdout = execSync(`npx qiita new "${title}"`, { encoding: 'utf-8' });
  console.log(stdout);

  // The output usually contains the path to the newly created file, or we can just find the newest file in public/
  const publicDir = path.join(__dirname, '..', 'public');
  const files = fs.readdirSync(publicDir)
    .filter(f => f.endsWith('.md'))
    .map(f => ({
      name: f,
      time: fs.statSync(path.join(publicDir, f)).mtime.getTime()
    }))
    .sort((a, b) => b.time - a.time);

  if (files.length > 0) {
    const newestFile = path.join(publicDir, files[0].name);
    console.log(`Targeting newest file: ${files[0].name}`);
    
    let content = fs.readFileSync(newestFile, 'utf-8');
    
    // Replace private: false with private: true
    if (content.includes('private: false')) {
      content = content.replace('private: false', 'private: true');
      fs.writeFileSync(newestFile, content, 'utf-8');
      console.log(`✅ Successfully set 'private: true' in ${files[0].name}`);
    } else {
      console.log(`⚠️ 'private: false' not found in frontmatter. Check manually.`);
    }
  }

} catch (error) {
  console.error('Error creating article:', error.message);
  process.exit(1);
}
